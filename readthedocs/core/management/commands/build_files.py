from django.core.management.base import BaseCommand
from projects import tasks
from projects.models import Project

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        if not len(args):
            for p in Project.objects.all():
                print "Indexing %s" % p
                tasks.fileify(p)
        else:
            for slug in args:
                p = Project.objects.get(slug=slug)
                print "Indexing %s" % p
                tasks.fileify(p)
