from django.core.management.base import BaseCommand
from optparse import make_option
from projects import tasks
from projects.models import Project
from builds.models import Version

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """
    option_list = BaseCommand.option_list + (
        make_option('-V',
            dest='version',
            default=None,
            help='Build a version, or all versions'
            ),
        )

    def handle(self, *args, **options):
        version = options['version']
        if len(args):
            for slug in args:
                if version and version != "all":
                    print "Updating version %s for %s" % (version, slug)
                    for version in Version.objects.filter(project__slug=slug,
                                                          slug=version):
                        tasks.move_docs(version.project, version)
                elif version == "all":
                    print "Updating all versions for %s" % slug
                    for version in Version.objects.filter(project__slug=slug,
                                                          active=True,
                                                          uploaded=False):
                        tasks.move_docs(version.project, version)
                else:
                    print "Updating latest version"
                    p = Project.objects.get(slug=slug)
                    v = p.versions.get(slug='latest')
                    tasks.move_docs(p, v)
        else:
            print "Updating all versions"
            for version in Version.objects.all():
                tasks.move_docs(version.project, version)
