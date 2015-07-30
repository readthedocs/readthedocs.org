"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import fnmatch
import os
import shutil
import json
import logging
import socket
import requests
import datetime

from celery import task
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from slumber.exceptions import HttpClientError

from builds.constants import LATEST
from builds.models import Build, Version
from core.utils import send_email, run_on_app_servers
from doc_builder.loader import get_builder_class
from doc_builder.base import restoring_chdir
from doc_builder.environments import DockerEnvironment
from projects.exceptions import ProjectImportError
from projects.models import ImportedFile, Project
from projects.utils import run, make_api_version, make_api_project
from projects.constants import LOG_TEMPLATE
from builds.constants import STABLE
from projects import symlinks
from privacy.loader import Syncer
from search.parse_json import process_all_json_files
from search.utils import process_mkdocs_json
from restapi.utils import index_search_request
from vcs_support import utils as vcs_support_utils
from api.client import api as api_v1
from restapi.client import api as api_v2

try:
    from readthedocs.projects.signals import before_vcs, after_vcs, before_build, after_build
except:
    from projects.signals import before_vcs, after_vcs, before_build, after_build


log = logging.getLogger(__name__)

HTML_ONLY = getattr(settings, 'HTML_ONLY_PROJECTS', ())


@task(default_retry_delay=7 * 60, max_retries=5)
@restoring_chdir
def update_docs(pk, version_pk=None, build_pk=None, record=True, docker=False,
                search=True, force=False, intersphinx=True, localmedia=True,
                basic=False, **kwargs):
    """
    The main entry point for updating documentation.

    It handles all of the logic around whether a project is imported or we
    created it.  Then it will build the html docs and other requested parts.

    `pk`
        Primary key of the project to update

    `record`
        Whether or not to keep a record of the update in the database. Useful
        for preventing changes visible to the end-user when running commands
        from the shell, for example.

    """
    start_time = datetime.datetime.utcnow()
    try:
        project_data = api_v1.project(pk).get()
    except HttpClientError:
        log.exception(LOG_TEMPLATE.format(project=pk, version='', msg='Failed to get project data on build. Erroring.'))
    project = make_api_project(project_data)
    # Don't build skipped projects
    if project.skip:
        log.info(LOG_TEMPLATE.format(project=project.slug, version='', msg='Skipping'))
        return
    else:
        log.info(LOG_TEMPLATE.format(project=project.slug, version='', msg='Building'))
    version = ensure_version(project, version_pk)
    build = create_build(build_pk)
    results = {}

    # Build Servery stuff
    try:
        record_build(build=build, record=record, results=results, state='cloning')
        vcs_results = setup_vcs(version, build)
        if vcs_results:
            results.update(vcs_results)

        if project.documentation_type == 'auto':
            update_documentation_type(version)

        if docker or settings.DOCKER_ENABLE:
            record_build(build=build, record=record, results=results, state='building')
            docker = DockerEnvironment(version)
            build_results = docker.build()
            results.update(build_results)
        else:
            record_build(build=build, record=record, results=results, state='installing')
            setup_results = setup_environment(version)
            results.update(setup_results)

            record_build(build=build, record=record, results=results, state='building')
            build_results = build_docs(version, force, search, localmedia)
            results.update(build_results)

    except vcs_support_utils.LockTimeout, e:
        results['checkout'] = (423, "", "Version locked, retrying in 5 minutes.")
        log.info(LOG_TEMPLATE.format(project=version.project.slug,
                                     version=version.slug, msg="Unable to lock, will retry"))
        # http://celery.readthedocs.org/en/3.0/userguide/tasks.html#retrying
        # Should completely retry the task for us until max_retries is exceeded
        update_docs.retry(exc=e, throw=False)
    except ProjectImportError, e:
        results['checkout'] = (404, "", 'Failed to import project; skipping build.\n\nError\n-----\n\n%s' % e.message)
        # Close out build in finally with error.
        pass
    except Exception, e:
        log.error(LOG_TEMPLATE.format(project=version.project.slug,
                                      version=version.slug, msg="Top-level Build Failure"), exc_info=True)
        results['checkout'] = (404, "", 'Top-level Build Failure: %s' % e.message)
    finally:
        record_build(build=build, record=record, results=results, state='finished', start_time=start_time)
        record_pdf(record=record, results=results, state='finished', version=version)
        log.info(LOG_TEMPLATE.format(project=version.project.slug, version='', msg='Build finished'))

    build_id = build.get('id')
    # Web Server Tasks
    if build_id:
        finish_build.delay(
            version_pk=version.pk,
            build_pk=build_id,
            hostname=socket.gethostname(),
            html=results.get('html', [404])[0] == 0,
            localmedia=results.get('localmedia', [404])[0] == 0,
            search=results.get('search', [404])[0] == 0,
            pdf=version.project.enable_pdf_build,
            epub=version.project.enable_epub_build,
        )


def ensure_version(project, version_pk):
    """
    Ensure we're using a sane version.
    """

    if version_pk:
        version_data = api_v1.version(version_pk).get()
    else:
        version_data = api_v1.version(project.slug).get(slug=LATEST)['objects'][0]
    version = make_api_version(version_data)
    return version


def update_documentation_type(version):
    """
    Automatically determine the doc type for a user.
    """

    checkout_path = version.project.checkout_path(version.slug)
    os.chdir(checkout_path)
    files = run('find .')[1].split('\n')
    markdown = sphinx = 0
    for filename in files:
        if fnmatch.fnmatch(filename, '*.md') or fnmatch.fnmatch(filename, '*.markdown'):
            markdown += 1
        elif fnmatch.fnmatch(filename, '*.rst'):
            sphinx += 1
    ret = 'sphinx'
    if markdown > sphinx:
        ret = 'mkdocs'
    project_data = api_v2.project(version.project.pk).get()
    project_data['documentation_type'] = ret
    api_v2.project(version.project.pk).put(project_data)
    version.project.documentation_type = ret


def docker_build(version, search=True, force=False, intersphinx=True,
                 localmedia=True):
    """
    The code that executes inside of docker
    """
    environment_results = setup_environment(version)
    results = build_docs(version=version, force=force, search=search,
                         localmedia=localmedia)
    results.update(environment_results)
    return results


def setup_vcs(version, build):
    """
    Update the checkout of the repo to make sure it's the latest.
    This also syncs versions in the DB.
    """

    log.info(LOG_TEMPLATE.format(project=version.project.slug,
                                 version=version.slug, msg='Updating docs from VCS'))
    try:
        update_output = update_imported_docs(version.pk)
        commit = version.project.vcs_repo(version.slug).commit
        if commit:
            build['commit'] = commit
    except ProjectImportError:
        log.error(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug,
                                      msg='Failed to import project; skipping build'), exc_info=True)
        raise
    return update_output


@task()
def update_imported_docs(version_pk):
    """
    Check out or update the given project's repository.
    """
    version_data = api_v1.version(version_pk).get()
    version = make_api_version(version_data)
    project = version.project
    ret_dict = {}

    # Make Dirs
    if not os.path.exists(project.doc_path):
        os.makedirs(project.doc_path)

    if not project.vcs_repo():
        raise ProjectImportError(("Repo type '{0}' unknown".format(project.repo_type)))

    with project.repo_nonblockinglock(version=version,
                                      max_lock_age=getattr(settings, 'REPO_LOCK_SECONDS', 30)):

        before_vcs.send(sender=version)
        # Get the actual code on disk
        if version:
            log.info(
                LOG_TEMPLATE.format(
                    project=project.slug,
                    version=version.slug,
                    msg='Checking out version {slug}: {identifier}'.format(
                        slug=version.slug,
                        identifier=version.identifier
                    )
                )
            )
            version_slug = version.slug
            version_repo = project.vcs_repo(version_slug)
            ret_dict['checkout'] = version_repo.checkout(
                version.identifier,
            )
        else:
            # Does this ever get called?
            log.info(LOG_TEMPLATE.format(
                project=project.slug, version=version.slug, msg='Updating to latest revision'))
            version_slug = LATEST
            version_repo = project.vcs_repo(version_slug)
            ret_dict['checkout'] = version_repo.update()

        after_vcs.send(sender=version)

        # Update tags/version

        version_post_data = {'repo': version_repo.repo_url}

        if version_repo.supports_tags:
            version_post_data['tags'] = [
                {'identifier': v.identifier,
                 'verbose_name': v.verbose_name,
                 } for v in version_repo.tags
            ]

        if version_repo.supports_branches:
            version_post_data['branches'] = [
                {'identifier': v.identifier,
                 'verbose_name': v.verbose_name,
                 } for v in version_repo.branches
            ]

        try:
            api_v2.project(project.pk).sync_versions.post(version_post_data)
        except Exception, e:
            print "Sync Versions Exception: %s" % e.message
    return ret_dict


def setup_environment(version):
    """
    Build the virtualenv and install the project into it.

    Always build projects with a virtualenv.
    """
    ret_dict = {}
    project = version.project
    build_dir = os.path.join(project.venv_path(version=version.slug), 'build')
    if os.path.exists(build_dir):
        log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='Removing existing build dir'))
        shutil.rmtree(build_dir)
    if project.use_system_packages:
        site_packages = '--system-site-packages'
    else:
        site_packages = '--no-site-packages'
    # Here the command has been modified to support different
    # interpreters.
    ret_dict['venv'] = run(
        '{cmd} {site_packages} {path}'.format(
            cmd='{interpreter} -m virtualenv'.format(
                interpreter=project.python_interpreter),
            site_packages=site_packages,
            path=project.venv_path(version=version.slug)
        )
    )
    # Other code expects sphinx-build to be installed inside the
    # virtualenv.  Using the -I option makes sure it gets installed
    # even if it is already installed system-wide (and
    # --system-site-packages is used)
    if project.use_system_packages:
        ignore_option = '-I'
    else:
        ignore_option = ''

    requirements = ' '.join([
        'sphinx==1.3.1',
        'Pygments==2.0.2',
        'virtualenv==13.1.0',
        'setuptools==18.0.1',
        'docutils==0.11',
        'mkdocs==0.14.0',
        'mock==1.0.1',
        'pillow==2.6.1',
        'readthedocs-sphinx-ext==0.5.4',
        'sphinx-rtd-theme==0.1.8',
        'alabaster>=0.7,<0.8,!=0.7.5',
        'recommonmark==0.1.1',
        'git+https://github.com/rtfd/readthedocs-build',
    ])

    wheeldir = os.path.join(settings.SITE_ROOT, 'deploy', 'wheels')
    ret_dict['doc_builder'] = run(
        (
            '{cmd} install --use-wheel --find-links={wheeldir} -U '
            '{ignore_option} {requirements}'
        ).format(
            cmd=project.venv_bin(version=version.slug, bin='pip'),
            ignore_option=ignore_option,
            wheeldir=wheeldir,
            requirements=requirements,
        )
    )

    # Handle requirements

    requirements_file_path = project.requirements_file
    checkout_path = project.checkout_path(version.slug)
    if not requirements_file_path:
        builder_class = get_builder_class(project.documentation_type)
        docs_dir = builder_class(version).docs_dir()
        for path in [docs_dir, '']:
            for req_file in ['pip_requirements.txt', 'requirements.txt']:
                test_path = os.path.join(checkout_path, path, req_file)
                print('Testing %s' % test_path)
                if os.path.exists(test_path):
                    requirements_file_path = test_path
                    break

    if requirements_file_path:
        os.chdir(checkout_path)
        ret_dict['requirements'] = run(
            '{cmd} install --exists-action=w -r {requirements}'.format(
                cmd=project.venv_bin(version=version.slug, bin='pip'),
                requirements=requirements_file_path))

    # Handle setup.py

    os.chdir(project.checkout_path(version.slug))
    if os.path.isfile("setup.py"):
        if getattr(settings, 'USE_PIP_INSTALL', False):
            ret_dict['install'] = run(
                '{cmd} install --ignore-installed .'.format(
                    cmd=project.venv_bin(version=version.slug, bin='pip')))
        else:
            ret_dict['install'] = run(
                '{cmd} setup.py install --force'.format(
                    cmd=project.venv_bin(version=version.slug,
                                         bin='python')))
    else:
        ret_dict['install'] = (999, "", "No setup.py, skipping install")
    return ret_dict


@task()
def build_docs(version, force, search, localmedia):
    """
    This handles the actual building of the documentation
    """

    project = version.project
    results = {}

    before_build.send(sender=version)

    with project.repo_nonblockinglock(version=version,
                                      max_lock_age=getattr(settings, 'REPO_LOCK_SECONDS', 30)):
        html_builder = get_builder_class(project.documentation_type)(version)
        if force:
            html_builder.force()
        html_builder.append_conf()
        results['html'] = html_builder.build()
        if results['html'][0] == 0:
            html_builder.move()

        # Gracefully attempt to move files via task on web workers.
        try:
            move_files.delay(
                version_pk=version.pk,
                html=True,
                hostname=socket.gethostname(),
            )
        except socket.error:
            pass

        fake_results = (999, "Project Skipped, Didn't build",
                        "Project Skipped, Didn't build")
        if 'mkdocs' in project.documentation_type:
            if search:
                try:
                    search_builder = get_builder_class('mkdocs_json')(version)
                    results['search'] = search_builder.build()
                    if results['search'][0] == 0:
                        search_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(
                        project=project.slug, version=version.slug, msg="JSON Build Error"), exc_info=True)

        if 'sphinx' in project.documentation_type:
            # Search builder. Creates JSON from docs and sends it to the
            # server.
            if search:
                try:
                    search_builder = get_builder_class('sphinx_search')(version)
                    results['search'] = search_builder.build()
                    if results['search'][0] == 0:
                        # Copy json for safe keeping
                        search_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(
                        project=project.slug, version=version.slug, msg="JSON Build Error"), exc_info=True)
            # Local media builder for singlepage HTML download archive
            if localmedia:
                try:
                    localmedia_builder = get_builder_class('sphinx_singlehtmllocalmedia')(version)
                    results['localmedia'] = localmedia_builder.build()
                    if results['localmedia'][0] == 0:
                        localmedia_builder.move()
                except:
                    log.error(LOG_TEMPLATE.format(
                        project=project.slug, version=version.slug, msg="Local Media HTML Build Error"), exc_info=True)

            # Optional build steps
            if version.project.slug not in HTML_ONLY and not project.skip:
                if project.enable_pdf_build:
                    pdf_builder = get_builder_class('sphinx_pdf')(version)
                    results['pdf'] = pdf_builder.build()
                    # Always move pdf results even when there's an error.
                    # if pdf_results[0] == 0:
                    pdf_builder.move()
                else:
                    results['pdf'] = fake_results
                if project.enable_epub_build:
                    epub_builder = get_builder_class('sphinx_epub')(version)
                    results['epub'] = epub_builder.build()
                    if results['epub'][0] == 0:
                        epub_builder.move()
                else:
                    results['epub'] = fake_results

    after_build.send(sender=version)

    return results


def create_build(build_pk):
    """
    Old placeholder for build creation. Now it just gets it from the database.
    """
    if build_pk:
        build = api_v1.build(build_pk).get()
        for key in ['project', 'version', 'resource_uri', 'absolute_uri']:
            if key in build:
                del build[key]
    else:
        build = {}
    return build


def record_build(record, build, results, state, start_time=None):
    """
    Record a build by hitting the API.

    Returns nothing
    """

    if not record:
        return None

    build['builder'] = socket.gethostname()

    setup_steps = ['checkout', 'venv', 'doc_builder', 'requirements', 'install']
    output_steps = ['html']
    all_steps = setup_steps + output_steps

    build['state'] = state
    if 'html' in results:
        build['success'] = results['html'][0] == 0
    else:
        build['success'] = False

    # Set global state
    # for step in all_steps:
    #     if results.get(step, False):
    #         if results.get(step)[0] != 0:
    #             results['success'] = False

    build['exit_code'] = max([results.get(step, [0])[0] for step in all_steps])

    build['setup'] = build['setup_error'] = ""
    build['output'] = build['error'] = ""

    if start_time:
        build['length'] = (datetime.datetime.utcnow() - start_time).total_seconds()

    for step in setup_steps:
        if step in results:
            build['setup'] += "\n\n%s\n-----\n\n" % step
            try:
                build['setup'] += results.get(step)[1]
            except (IndexError, TypeError):
                pass
            build['setup_error'] += "\n\n%s\n-----\n\n" % step
            try:
                build['setup_error'] += results.get(step)[2]
            except (IndexError, TypeError):
                pass

    for step in output_steps:
        if step in results:
            build['output'] += "\n\n%s\n-----\n\n" % step
            try:
                build['output'] += results.get(step)[1]
            except (IndexError, TypeError):
                pass
            build['error'] += "\n\n%s\n-----\n\n" % step
            try:
                build['error'] += results.get(step)[2]
            except (IndexError, TypeError):
                pass

    # Attempt to stop unicode errors on build reporting
    for key, val in build.items():
        if isinstance(val, basestring):
            build[key] = val.decode('utf-8', 'ignore')

    try:
        api_v1.build(build['id']).put(build)
    except Exception:
        log.error("Unable to post a new build", exc_info=True)


def record_pdf(record, results, state, version):
    if not record or 'sphinx' not in version.project.documentation_type:
        return None
    if not version.project.enable_pdf_build:
        return None
    try:
        if 'pdf' in results:
            pdf_exit = results['pdf'][0]
            pdf_success = pdf_exit == 0
            pdf_output = results['pdf'][1]
            pdf_error = results['pdf'][2]
        else:
            pdf_exit = 999
            pdf_success = False
            pdf_output = pdf_error = "PDF Failed"

        pdf_output = pdf_output.decode('utf-8', 'ignore')
        pdf_error = pdf_error.decode('utf-8', 'ignore')

        if 'Output written on' in pdf_output:
            pdf_success = True

        api_v1.build.post(dict(
            state=state,
            project='/api/v1/project/%s/' % version.project.pk,
            version='/api/v1/version/%s/' % version.pk,
            success=pdf_success,
            type='pdf',
            output=pdf_output,
            error=pdf_error,
            exit_code=pdf_exit,
            builder=socket.gethostname(),
        ))
    except Exception:
        log.error(LOG_TEMPLATE.format(project=version.project.slug,
                                      version=version.slug, msg="Unable to post a new build"), exc_info=True)


###########
# Web tasks
###########


@task(queue='web')
def finish_build(version_pk, build_pk, hostname=None, html=False,
                 localmedia=False, search=False, pdf=False, epub=False):
    """
    Build Finished, do house keeping bits
    """
    version = Version.objects.get(pk=version_pk)
    build = Build.objects.get(pk=build_pk)

    if html:
        version.active = True
        version.built = True
        version.save()

    move_files(
        version_pk=version_pk,
        hostname=hostname,
        html=html,
        localmedia=localmedia,
        search=search,
        pdf=pdf,
        epub=epub,
    )

    symlinks.symlink_cnames(version)
    symlinks.symlink_translations(version)
    symlinks.symlink_subprojects(version)
    if version.project.single_version:
        symlinks.symlink_single_version(version)
    else:
        symlinks.remove_symlink_single_version(version)

    # Delayed tasks
    update_static_metadata.delay(version.project.pk)
    fileify.delay(version.pk, commit=build.commit)
    update_search.delay(version.pk, commit=build.commit)
    if not html and version.slug != STABLE and build.exit_code != 423:
        send_notifications.delay(version.pk, build_pk=build.pk)


@task(queue='web')
def move_files(version_pk, hostname, html=False, localmedia=False, search=False, pdf=False, epub=False):
    version = Version.objects.get(pk=version_pk)

    if html:
        from_path = version.project.artifact_path(version=version.slug, type=version.project.documentation_type)
        target = version.project.rtd_build_path(version.slug)
        Syncer.copy(from_path, target, host=hostname)

    if 'sphinx' in version.project.documentation_type:
        if localmedia:
            from_path = version.project.artifact_path(version=version.slug, type='sphinx_localmedia')
            to_path = version.project.get_production_media_path(type='htmlzip', version_slug=version.slug, include_file=False)
            Syncer.copy(from_path, to_path, host=hostname)
        if search:
            from_path = version.project.artifact_path(version=version.slug, type='sphinx_search')
            to_path = version.project.get_production_media_path(type='json', version_slug=version.slug, include_file=False)
            Syncer.copy(from_path, to_path, host=hostname)
        # Always move PDF's because the return code lies.
        if pdf:
            from_path = version.project.artifact_path(version=version.slug, type='sphinx_pdf')
            to_path = version.project.get_production_media_path(type='pdf', version_slug=version.slug, include_file=False)
            Syncer.copy(from_path, to_path, host=hostname)
        if epub:
            from_path = version.project.artifact_path(version=version.slug, type='sphinx_epub')
            to_path = version.project.get_production_media_path(type='epub', version_slug=version.slug, include_file=False)
            Syncer.copy(from_path, to_path, host=hostname)

    if 'mkdocs' in version.project.documentation_type:
        if search:
            from_path = version.project.artifact_path(version=version.slug, type='mkdocs_json')
            to_path = version.project.get_production_media_path(type='json', version_slug=version.slug, include_file=False)
            Syncer.copy(from_path, to_path, host=hostname)


@task(queue='web')
def update_search(version_pk, commit):

    version = Version.objects.get(pk=version_pk)

    if 'sphinx' in version.project.documentation_type:
        page_list = process_all_json_files(version, build_dir=False)
    elif 'mkdocs' in version.project.documentation_type:
        page_list = process_mkdocs_json(version, build_dir=False)
    else:
        log.error('Unknown documentation type: %s' % version.project.documentation_type)
        return

    log_msg = ' '.join([page['path'] for page in page_list])
    log.info("(Search Index) Sending Data: %s [%s]" % (version.project.slug, log_msg))
    index_search_request(
        version=version,
        page_list=page_list,
        commit=commit,
        project_scale=0,
        page_scale=0,
        # Don't index sections to speed up indexing.
        # They aren't currently exposed anywhere.
        section=False,
    )


@task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is a prereq for indexing the docs for search.
    It also causes celery-haystack to kick off an index of the file.
    """
    version = Version.objects.get(pk=version_pk)
    project = version.project

    if not commit:
        log.info(LOG_TEMPLATE.format(
            project=project.slug, version=version.slug, msg='Imported File not being built because no commit information'))

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(LOG_TEMPLATE.format(
            project=project.slug, version=version.slug, msg='Creating ImportedFiles'))
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath = os.path.join(root.replace(path, '').lstrip('/'),
                                           filename.lstrip('/'))
                    obj, created = ImportedFile.objects.get_or_create(
                        project=project,
                        version=version,
                        path=dirpath,
                        name=filename,
                        commit=commit,
                    )
                    if not created:
                        obj.save()
        # Delete ImportedFiles from previous versions
        ImportedFile.objects.filter(project=project, version=version).exclude(commit=commit).delete()
    else:
        log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='No ImportedFile files'))


@task(queue='web')
def send_notifications(version_pk, build_pk):
    version = Version.objects.get(pk=version_pk)
    build = Build.objects.get(pk=build_pk)

    for hook in version.project.webhook_notifications.all():
        webhook_notification(version, build, hook.url)
    for email in version.project.emailhook_notifications.all().values_list('email', flat=True):
        email_notification(version, build, email)


def email_notification(version, build, email):
    log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug,
                                  msg='sending email to: %s' % email))
    context = {'version': version,
               'project': version.project,
               'build': build,
               'build_url': 'https://{0}{1}'.format(
                   getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
                   build.get_absolute_url()),
               'unsub_url': 'https://{0}{1}'.format(
                   getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'),
                   reverse('projects_notifications', args=[version.project.slug])),
               }

    if build.commit:
        title = _('Failed: {project.name} ({commit})').format(commit=build.commit[:8], **context)
    else:
        title = _('Failed: {project.name} ({version.verbose_name})').format(**context)

    send_email(
        email,
        title,
        template='projects/email/build_failed.txt',
        template_html='projects/email/build_failed.html',
        context=context
    )


def webhook_notification(version, build, hook_url):
    data = json.dumps({
        'name': project.name,
        'slug': project.slug,
        'build': {
            'id': build.id,
            'success': build.success,
            'date': build.date.strftime('%Y-%m-%d %H:%M:%S'),
        }
    })
    log.debug(LOG_TEMPLATE.format(project=project.slug, version='', msg='sending notification to: %s' % hook_url))
    requests.post(hook_url, data=data)


@task(queue='web')
def update_static_metadata(project_pk, path=None):
    """Update static metadata JSON file

    Metadata settings include the following project settings:

    version
      The default version for the project, default: `latest`

    language
      The default language for the project, default: `en`

    languages
      List of languages built by linked translation projects.
    """
    project = Project.objects.get(pk=project_pk)
    if not path:
        path = project.static_metadata_path()

    log.info(LOG_TEMPLATE.format(
        project=project.slug,
        version='',
        msg='Updating static metadata',
    ))
    translations = [trans.language for trans in project.translations.all()]
    languages = set(translations)
    # Convert to JSON safe types
    metadata = {
        'version': project.default_version,
        'language': project.language,
        'languages': list(languages),
        'single_version': project.single_version,
    }
    try:
        fh = open(path, 'w+')
        json.dump(metadata, fh)
        fh.close()
        Syncer.copy(path, path, host=socket.gethostname(), file=True)
    except (AttributeError, IOError) as e:
        log.debug(LOG_TEMPLATE.format(
            project=project.slug,
            version='',
            msg='Cannot write to metadata.json: {0}'.format(e)
        ))


#@periodic_task(run_every=crontab(hour="*", minute="*/5", day_of_week="*"))
def update_docs_pull(record=False, force=False):
    """
    A high-level interface that will update all of the projects.

    This is mainly used from a cronjob or management command.
    """
    for version in Version.objects.filter(built=True):
        try:
            update_docs(
                pk=version.project.pk, version_pk=version.pk, record=record)
        except Exception, e:
            log.error("update_docs_pull failed", exc_info=True)

##############
# Random Tasks
##############


@task()
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers
    can kill things on the build server.
    """
    log.info("Removing %s" % path)
    shutil.rmtree(path)


@task(queue='web')
def clear_artifacts(version_pk):
    """ Remove artifacts from the web servers. """
    version = Version.objects.get(pk=version_pk)
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='pdf', version_slug=version.slug))
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='epub', version_slug=version.slug))
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='htmlzip', version_slug=version.slug))
    run_on_app_servers('rm -rf %s' % version.project.rtd_build_path(version=version.slug))
