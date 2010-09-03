from django.core.management.base import BaseCommand
from projects import tasks
from projects.models import Project

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """
    def handle(self, *args, **kwargs):
        if not len(args):
            tasks.update_docs_pull()
        else:
            for slug in args:
                p = Project.objects.get(slug=slug)
                print "Building %s" % p
                tasks.update_docs(p.pk)


