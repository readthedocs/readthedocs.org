import logging

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _
from optparse import make_option
from projects import tasks
from projects.models import Project
from builds.models import Version

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    option_list = BaseCommand.option_list + (
        make_option('-p',
            action='store_true',
            dest='pdf',
            default=False,
            help=_('Make a pdf')
            ),
        make_option('-r',
            action='store_true',
            dest='record',
            default=False,
            help=_('Make a Build')
            ),
        make_option('-f',
            action='store_true',
            dest='force',
            default=False,
            help='Force a build in sphinx'
            ),
        make_option('-V',
            dest='version',
            default=None,
            help=_('Build a version, or all versions')
            )
        )

    def handle(self, *args, **options):
        make_pdf = options['pdf']
        record = options['record']
        force = options['force']
        version = options['version']
        if len(args):
            for slug in args:
                if version and version != "all":
<<<<<<< HEAD
                    log.info("Updating version %s for %s" % (version, slug))
=======
                    print _("Updating version") + " %s " + _("for") + " %s)" % (version, slug)
>>>>>>> 8249b5c288c3eba2e845684ba818f61e71a95a12
                    for version in Version.objects.filter(project__slug=slug,
                                                          slug=version):
                        tasks.update_docs(version.project_id,
                                          pdf=make_pdf,
                                          record=False,
                                          version_pk=version.pk)
                elif version == "all":
<<<<<<< HEAD
                    log.info("Updating all versions for %s" % slug)
=======
                    print _("Updating all versions for %s") % slug
>>>>>>> 8249b5c288c3eba2e845684ba818f61e71a95a12
                    for version in Version.objects.filter(project__slug=slug,
                                                          active=True,
                                                          uploaded=False):
                        tasks.update_docs(pk=version.project_id,
                                          pdf=make_pdf,
                                          record=False,
                                          version_pk=version.pk)
                else:
                    p = Project.objects.get(slug=slug)
<<<<<<< HEAD
                    log.info("Building %s" % p)
                    tasks.update_docs(pk=p.pk, pdf=make_pdf, force=force)
        else:
            if version == "all":
                log.info("Updating all versions")
=======
                    print _("Building %s") % p
                    tasks.update_docs(pk=p.pk, pdf=make_pdf, force=force)
        else:
            if version == "all":
                print _("Updating all versions")
>>>>>>> 8249b5c288c3eba2e845684ba818f61e71a95a12
                for version in Version.objects.filter(active=True,
                                                      uploaded=False):
                    tasks.update_docs(pk=version.project_id,
                                      pdf=make_pdf,
                                      record=record,
                                      force=force,
                                      version_pk=version.pk)
            else:
<<<<<<< HEAD
                log.info("Updating all docs")
=======
                print _("Updating all docs")
>>>>>>> 8249b5c288c3eba2e845684ba818f61e71a95a12
                tasks.update_docs_pull(pdf=make_pdf,
                                       record=record,
                                       force=force)
 
    @property
    def help(self):
        return Command.__doc__
 
