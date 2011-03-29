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
                print "Updating all versions for %s" % slug
                for version in Version.objects.filter(project__slug=slug,
                                                      active=True):
                    path = version.project.rtd_build_path(version.slug)
                    tasks.copy_to_app_servers(path, path)
        else:
            print "Updating all versions"
            for version in Version.objects.filter(active=True):
                try:
                    path = version.project.rtd_build_path(version.slug)
                    tasks.copy_to_app_servers(path, path)
                except Exception, e:
                    print "Error: %s" % e
