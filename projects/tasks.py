"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""

from builds.models import Build, Version
from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from django.conf import settings
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from projects.exceptions import ProjectImportError
from projects.models import Project, ImportedFile
from projects.utils import run, sanitize_conf, slugify_uniquely
from vcs_support.base import get_backend
import decimal
import fnmatch
import glob
import os
import re


ghetto_hack = re.compile(r'(?P<key>.*)\s*=\s*u?\[?[\'\"](?P<value>.*)[\'\"]\]?')

latex_re = re.compile('the LaTeX files are in (.*)\.')


@task
def update_docs(pk, record=True, pdf=False, version_pk=None):
    """
    A Celery task that updates the documentation for a project.
    """
    project = Project.objects.live().get(pk=pk)
    if project.skip:
        print "Skipping %s" % project
        return
    if version_pk:
        version = Version.objects.get(pk=version_pk)
    else:
        version = None
    print "Building %s" % project
    path = project.user_doc_path
    if not os.path.exists(path):
        os.makedirs(path)

    if project.is_imported:
        try:
            update_imported_docs(project, version)
        except ProjectImportError, err:
            print("Error importing project: %s. Skipping build." % err)
            return
        else:
            scrape_conf_file(project)
    else:
        update_created_docs(project)

    # kick off a build
    (ret, out, err) = build_docs(project, pdf)
    if not 'no targets are out of date.' in out:
        if record:
            Build.objects.create(project=project, success=ret==0, output=out, error=err)
        if ret == 0:
            print "Build OK"
            if version:
                version.built = True
                version.save()
            move_docs(project, version)
        else:
            print "Build ERROR"
            print err
    else:
        print "Build Unchanged"


def update_imported_docs(project, version):
    """
    Check out or update the given project's repository.
    """
    backend = get_backend(project.repo_type)
    if not backend:
        raise ProjectImportError("Repo type '%s' unknown" % project.repo_type)
    working_dir = os.path.join(project.user_doc_path, project.slug)
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    vcs_repo = backend(project.repo, working_dir)
    if version:
        print 'Checking out version %s' % version.identifier
        vcs_repo.checkout(version.identifier)
    else:
        print 'Updating to latest revision'
        vcs_repo.update()
        
        # check tags/version
        if vcs_repo.supports_tags:
            tags = vcs_repo.get_tags()
            old_tags = Version.objects.filter(project=project).values_list('identifier', flat=True)
            for tag in tags:
                if tag.identifier in old_tags:
                    continue
                slug = slugify_uniquely(Version, tag.verbose_name, 'slug', 255, project=project)
                Version.objects.create(
                    project=project,
                    slug=slug,
                    identifier=tag.identifier,
                    verbose_name=tag.verbose_name
                )
    
    fileify(project_slug=project.slug)


def scrape_conf_file(project):
    """Locate the given project's ``conf.py`` file and extract important
    settings, including copyright, theme, source suffix and version.
    """
    try:
        conf_dir = project.find('conf.py')[0]
    except IndexError:
        print("Could not find conf.py in %s" % project)
        return
    else:
        conf_dir = conf_dir.replace('/conf.py', '')

    os.chdir(conf_dir)
    lines = open('conf.py').readlines()
    data = {}
    for line in lines:
        match = ghetto_hack.search(line)
        if match:
            data[match.group(1).strip()] = match.group(2).strip()
    project.copyright = data.get('copyright', 'Unknown')
    project.theme = data.get('html_theme', 'default')
    #if project.theme not in [x[0] for x in DEFAULT_THEME_CHOICES]:
        #project.theme = 'default'
    project.suffix = data.get('source_suffix', '.rst')
    #project.extensions = data.get('extensions', '').replace('"', "'")
    project.path = os.getcwd()

    try:
        project.version = decimal.Decimal(data.get('version', '0.1.0'))
    except decimal.InvalidOperation:
        project.version = ''

    project.save()


def update_created_docs(project):
    # grab the root path for the generated docs to live at
    path = project.user_doc_path

    doc_root = os.path.join(path, project.slug, 'docs')

    if not os.path.exists(doc_root):
        os.makedirs(doc_root)

    project.path = doc_root
    project.save()

    project.write_index()

    for file in project.files.all():
        file.write_to_disk()


def build_docs(project, pdf):
    """
    A helper function for the celery task to do the actual doc building.
    """
    if not project.path:
        return ('','Conf file not found.',-1)
    try:
        profile = project.user.get_profile()
        if profile.whitelisted:
            print "Project whitelisted"
            sanitize_conf(project)
        else:
            print "Writing conf to disk"
            project.write_to_disk()
    except (OSError, SiteProfileNotAvailable, ObjectDoesNotExist):
        try:
            print "Writing conf to disk"
            project.write_to_disk()
        except (OSError, IOError):
            print "Conf file not found. Error writing to disk."
            return ('','Conf file not found. Error writing to disk.',-1)


    try:
        makes = [makefile for makefile in project.find('Makefile') if 'doc' in makefile]
        make_dir = makes[0].replace('/Makefile', '')
        os.chdir(make_dir)
        html_results = run('make html')
        if html_results[0] != 0:
            raise OSError
        if pdf:
            latex_results = run('make latex')
            match = latex_re.search(latex_results[1])
            if match:
                latex_dir = match.group(1).strip()
                os.chdir(latex_dir)
                pdf_results = run('make')
                pdf = glob.glob('*.pdf')[0]
                run('ln -s %s %s/%s.pdf' % (os.path.join(os.getcwd(), pdf),
                                            settings.MEDIA_ROOT,
                                            project.slug
                                           ))
    except (IndexError, OSError):
        os.chdir(project.path)
        html_results = run('sphinx-build -b html . _build/html')
    return html_results

def move_docs(project, version):
    pass

@task
def fileify(project_slug):
    project = Project.objects.get(slug=project_slug)
    path = project.full_html_path
    if path:
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fnmatch.fnmatch(filename, '*.html'):
                    dirpath =  os.path.join(root.replace(path, '').lstrip('/'), filename.lstrip('/'))
                    file, new = ImportedFile.objects.get_or_create(project=project,
                                                path=dirpath,
                                                name=filename)


@periodic_task(run_every=crontab(hour="2", minute="10", day_of_week="*"))
def update_docs_pull(pdf=False):
    for project in Project.objects.live():
        update_docs(pk=project.pk, record=False, pdf=pdf)
