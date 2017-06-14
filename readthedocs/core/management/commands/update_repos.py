"""
Custom management command to rebuild documentation for all projects.

Invoked via ``./manage.py update_repos``.
"""

from __future__ import absolute_import
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from readthedocs.projects import tasks
from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build

log = logging.getLogger(__name__)


class Command(BaseCommand):

    """Management command for rebuilding documentation on projects"""

    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option('-r',
                    action='store_true',
                    dest='record',
                    default=False,
                    help='Make a Build'),
        make_option('-f',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Force a build in sphinx'),
        make_option('-V',
                    dest='version',
                    default=None,
                    help='Build a version, or all versions')
    )

    def handle(self, *args, **options):
        record = options['record']
        force = options['force']
        version = options['version']
        if args:
            for slug in args:
                if version and version != "all":
                    log.info("Updating version %s for %s", version, slug)
                    for version in Version.objects.filter(project__slug=slug, slug=version):
                        trigger_build(project=version.project, version=version)
                elif version == "all":
                    log.info("Updating all versions for %s", slug)
                    for version in Version.objects.filter(project__slug=slug,
                                                          active=True,
                                                          uploaded=False):
                        tasks.update_docs.run(pk=version.project_id,
                                              record=False,
                                              version_pk=version.pk)
                else:
                    p = Project.all_objects.get(slug=slug)
                    log.info("Building %s", p)
                    trigger_build(project=p, force=force, record=record)
        else:
            if version == "all":
                log.info("Updating all versions")
                for version in Version.objects.filter(active=True,
                                                      uploaded=False):
                    tasks.update_docs.run(pk=version.project_id,
                                          record=record,
                                          force=force,
                                          version_pk=version.pk)
            else:
                log.info("Updating all docs")
                for project in Project.objects.all():
                    tasks.update_docs.run(pk=project.pk, record=record,
                                          force=force)
