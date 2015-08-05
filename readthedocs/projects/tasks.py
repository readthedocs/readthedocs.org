"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""
import fnmatch
import os
import sys
import shutil
import json
import logging
import socket
import requests
import datetime
import hashlib

from celery import task, Task
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from slumber.exceptions import HttpClientError
from docker import errors as docker_errors

from readthedocs.builds.constants import (LATEST, BUILD_STATE_TRIGGERED,
                                          BUILD_STATE_CLONING,
                                          BUILD_STATE_INSTALLING,
                                          BUILD_STATE_BUILDING,
                                          BUILD_STATE_FINISHED)
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import send_email, run_on_app_servers
from readthedocs.cdn.purge import purge
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.base import restoring_chdir
from readthedocs.doc_builder.environments import (LocalEnvironment,
                                                  DockerEnvironment)
from readthedocs.doc_builder.exceptions import (BuildEnvironmentError,
                                                BuildEnvironmentWarning)
from readthedocs.projects.exceptions import ProjectImportError
from readthedocs.projects.models import ImportedFile, Project
from readthedocs.projects.utils import run, make_api_version, make_api_project
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.builds.constants import STABLE
from readthedocs.projects import symlinks
from readthedocs.privacy.loader import Syncer
from readthedocs.search.parse_json import process_all_json_files
from readthedocs.search.utils import process_mkdocs_json
from readthedocs.restapi.utils import index_search_request
from readthedocs.vcs_support import utils as vcs_support_utils
from readthedocs.api.client import api as api_v1
from readthedocs.restapi.client import api as api_v2


try:
    from readthedocs.projects.signals import before_vcs, after_vcs, before_build, after_build
except:
    from readthedocs.projects.signals import before_vcs, after_vcs, before_build, after_build


log = logging.getLogger(__name__)

HTML_ONLY = getattr(settings, 'HTML_ONLY_PROJECTS', ())


class UpdateDocsTask(Task):
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
    max_retries=5
    default_retry_delay=(7 * 60)
    name = 'update_docs'

    def run(self, pk, version_pk=None, build_pk=None, record=True, docker=False,
            search=True, force=False, intersphinx=True, localmedia=True,
            basic=False, **kwargs):
        env_cls = LocalEnvironment
        if docker or settings.DOCKER_ENABLE:
            env_cls = DockerEnvironment

        # TODO Shouldn't this happen inside the build env? or which piece needs
        # to track this state? The build env or this task. It should only be one
        # of them. It does seem silly to have to require the build_env state
        self.project = self.get_project(pk)
        self.version = self.get_version(self.project, version_pk)
        self.build = self.get_build(build_pk)
        self.build_env = env_cls(project=self.project, version=self.version,
                                 build=self.build)
        with self.build_env:
            try:
                self.setup_vcs()
            except vcs_support_utils.LockTimeout, e:
                self.retry(exc=e, throw=False)
                raise BuildEnvironmentError(
                    'Version locked, retrying in 5 minutes.',
                    status_code=423
                )

            if self.project.documentation_type == 'auto':
                self.update_documentation_type()
            self.setup_environment()
            self.build_docs(force=force, search=search, localmedia=localmedia)

            build_id = self.build.get('id')

            # Web Server Tasks
            # TODO state here should be if the list of commands run in the environment
            # all passed. or maybe defer to a higher level concept here, on the build
            # environment
            # TODO replace the results check we some less jank ass bull shit
            if build_id:
                finish_build.delay(
                    version_pk=self.version.pk,
                    build_pk=build_id,
                    hostname=socket.gethostname(),
                    #html=results.get('html', [404])[0] == 0,
                    #localmedia=results.get('localmedia', [404])[0] == 0,
                    #search=results.get('search', [404])[0] == 0,
                    html=True,
                    localmedia=True,
                    search=True,
                    pdf=self.project.enable_pdf_build,
                    epub=self.project.enable_epub_build,
                )

    @staticmethod
    def get_project(project_pk):
        """
        Get project from API
        """
        try:
            project_data = api_v1.project(project_pk).get()
            project = make_api_project(project_data)
            if project.skip:
                # TODO more info on error here
                raise BuildEnvironmentError('Skipping project.')
            return project
        except HttpClientError:
            raise BuildEnvironmentError('Failed to get project data from API.')

    @staticmethod
    def get_version(project, version_pk):
        """
        Ensure we're using a sane version.
        """
        if version_pk:
            version_data = api_v1.version(version_pk).get()
        else:
            version_data = (api_v1
                            .version(project.slug)
                            .get(slug=LATEST)['objects'][0])
        return make_api_version(version_data)

    @staticmethod
    def get_build(build_pk):
        """
        Retrieve build object from API

        :param build_pk: Build primary key
        """
        build = {}
        if build_pk:
            build = api_v1.build(build_pk).get()
        return dict((key, val) for (key, val) in build.items()
                    if key not in ['project', 'version', 'resource_uri',
                                   'absolute_uri'])

    def update_documentation_type(self):
        """
        Automatically determine the doc type for a user.
        """
        # Keep this here for 'auto' projects
        ret = 'mkdocs'
        project_data = api_v2.project(self.project.pk).get()
        project_data['documentation_type'] = ret
        api_v2.project(self.project.pk).put(project_data)
        self.project.documentation_type = ret

    def setup_vcs(self):
        """
        Update the checkout of the repo to make sure it's the latest.
        This also syncs versions in the DB.

        :param build_env: Build environment
        """
        self.build_env.update_build(state=BUILD_STATE_CLONING)

        log.info(LOG_TEMPLATE
                 .format(project=self.project.slug,
                         version=self.version.slug,
                         msg='Updating docs from VCS'))
        try:
            update_output = update_imported_docs(self.version.pk)
            commit = self.project.vcs_repo(self.version.slug).commit
            if commit:
                self.build['commit'] = commit
        except ProjectImportError:
            raise BuildEnvironmentError('Failed to import project',
                                        status_code=404)

    def setup_environment(self):
        """
        Build the virtualenv and install the project into it.

        Always build projects with a virtualenv.

        :param build_env: Build environment to pass commands and execution through.
        """
        build_dir = os.path.join(
            self.project.venv_path(version=self.version.slug),
            'build')

        self.build_env.update_build(state=BUILD_STATE_INSTALLING)

        if os.path.exists(build_dir):
            log.info(LOG_TEMPLATE
                     .format(project=self.project.slug,
                             version=self.version.slug,
                             msg='Removing existing build directory'))
            shutil.rmtree(build_dir)
        site_packages = '--no-site-packages'
        if self.project.use_system_packages:
            site_packages = '--system-site-packages'
        self.build_env.run(
            self.project.python_interpreter,
            '-mvirtualenv',
            site_packages,
            self.project.venv_path(version=self.version.slug)
        )

        # Install requirements
        wheeldir = os.path.join(settings.SITE_ROOT, 'deploy', 'wheels')
        requirements = [
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
        ]

        cmd = [
            self.project.venv_bin(version=self.version.slug, bin='pip'),
            'install',
            '--use-wheel',
            '--find-links={0}'.format(wheeldir),
            '-U',
        ]
        if self.project.use_system_packages:
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            cmd.append('-I')
        cmd.extend(requirements)
        self.build_env.run(*cmd)

        # Handle requirements
        requirements_file_path = self.project.requirements_file
        checkout_path = self.project.checkout_path(self.version.slug)
        if not requirements_file_path:
            builder_class = get_builder_class(self.project.documentation_type)
            docs_dir = (builder_class(self.build_env)
                        .docs_dir())
            for path in [docs_dir, '']:
                for req_file in ['pip_requirements.txt', 'requirements.txt']:
                    test_path = os.path.join(checkout_path, path, req_file)
                    if os.path.exists(test_path):
                        requirements_file_path = test_path
                        break

        if requirements_file_path:
            self.build_env.run(
                self.project.venv_bin(version=self.version.slug, bin='pip'),
                'install',
                '--exists-action=w',
                '-r{0}'.format(requirements_file_path),
                cwd=checkout_path
            )

        # Handle setup.py
        checkout_path = self.project.checkout_path(self.version.slug)
        setup_path = os.path.join(checkout_path, 'setup.py')
        if os.path.isfile(setup_path):
            if getattr(settings, 'USE_PIP_INSTALL', False):
                self.build_env.run(
                    self.project.venv_bin(version=self.version.slug,
                                          bin='pip'),
                    'install',
                    '--ignore-installed',
                    '.',
                    cwd=checkout_path
                )
            else:
                self.build_env.run(
                    self.project.venv_bin(version=self.version.slug,
                                          bin='python'),
                    'setup.py',
                    'install',
                    '--force',
                    cwd=checkout_path
                )

    def build_docs(self, force, search, localmedia):
        """
        This handles the actual building of the documentation
        """
        self.build_env.update_build(state=BUILD_STATE_BUILDING)
        before_build.send(sender=self.version)

        with self.project.repo_nonblockinglock(
                    version=self.version,
                    max_lock_age=getattr(settings, 'REPO_LOCK_SECONDS', 30)
                ):
            self.build_docs_html(force=force)
            if 'mkdocs' in self.project.documentation_type:
                if search:
                    self.build_docs_class('mkdocs_json')
            if 'sphinx' in self.project.documentation_type:
                if search:
                    self.build_docs_class('sphinx_search')
                if localmedia:
                    self.build_docs_class('sphinx_singlehtmllocalmedia')

                if (self.project.slug not in HTML_ONLY):
                    if self.project.enable_pdf_build:
                        self.build_docs_class('sphinx_pdf')
                    if self.project.enable_epub_build:
                        self.build_docs_class('sphinx_epub')

        after_build.send(sender=self.version)

    def build_docs_html(self, force=False):
        html_builder = get_builder_class(self.project.documentation_type)(
            self.build_env
        )
        if force:
            html_builder.force()
        html_builder.append_conf()
        html_builder.build()

        # TODO this should be moved up to the general task run
        if self.build_env.successful:
            html_builder.move()

        # Gracefully attempt to move files via task on web workers.
        try:
            move_files.delay(
                version_pk=self.version.pk,
                html=True,
                hostname=socket.gethostname(),
            )
        except socket.error:
            # TODO do something here
            pass

    def build_docs_class(self, builder_class):
        """Build docs with additional doc backends

        These steps are not necessarily required for the build to halt, so we
        only raise a warning exception here. A hard error will halt the build
        process.
        """
        builder = get_builder_class(builder_class)(self.build_env)
        builder.build()
        builder.move()


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

# Web tasks
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

    if not pdf:
        clear_pdf_artifacts(version)
    if not epub:
        clear_epub_artifacts(version)

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

    if not project.cdn_enabled:
        return

    if not commit:
        log.info(LOG_TEMPLATE.format(
            project=project.slug, version=version.slug, msg='Imported File not being built because no commit information'))

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(LOG_TEMPLATE.format(
            project=version.project.slug, version=version.slug, msg='Creating ImportedFiles'))
        _manage_imported_files(version, path, commit)
    else:
        log.info(LOG_TEMPLATE.format(project=project.slug, version=version.slug, msg='No ImportedFile files'))


def _manage_imported_files(version, path, commit):
    changed_files = set()
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            dirpath = os.path.join(root.replace(path, '').lstrip('/'),
                                   filename.lstrip('/'))
            full_path = os.path.join(root, filename)
            md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest()
            try:
                obj, created = ImportedFile.objects.get_or_create(
                    project=version.project,
                    version=version,
                    path=dirpath,
                    name=filename,
                )
            except ImportedFile.MultipleObjectsReturned:
                log.exception('Error creating ImportedFile')
                continue
            if obj.md5 != md5:
                obj.md5 = md5
                changed_files.add(dirpath)
            if obj.commit != commit:
                obj.commit = commit
            obj.save()
    # Delete ImportedFiles from previous versions
    ImportedFile.objects.filter(project=version.project, version=version).exclude(commit=commit).delete()
    # Purge Cache
    purge(changed_files)


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
    project = version.project

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


def update_docs_pull(record=False, force=False):
    """
    A high-level interface that will update all of the projects.

    This is mainly used from a cronjob or management command.
    """
    for version in Version.objects.filter(built=True):
        try:
            update_docs = UpdateDocsTask
            update_docs.run(pk=version.project.pk, version_pk=version.pk,
                            record=record)
        except Exception, e:
            log.error("update_docs_pull failed", exc_info=True)


# Random Tasks
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
    clear_pdf_artifacts(version)
    clear_epub_artifacts(version)
    clear_htmlzip_artifacts(version)
    clear_html_artifacts(version)


def clear_pdf_artifacts(version):
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='pdf', version_slug=version.slug))


def clear_epub_artifacts(version):
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='epub', version_slug=version.slug))


def clear_htmlzip_artifacts(version):
    run_on_app_servers('rm -rf %s' % version.project.get_production_media_path(type='htmlzip', version_slug=version.slug))


def clear_html_artifacts(version):
    run_on_app_servers('rm -rf %s' % version.project.rtd_build_path(version=version.slug))
