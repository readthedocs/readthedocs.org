from django.core.management.base import BaseCommand
from projects import tasks
from projects.models import Project, ImportedFile
from builds.models import Version

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ImportedFile.objects.delete()
        if not len(args):
            for v in Version.objects.filter(slug='latest'):
                print "Indexing %s" % v
                try:
		    tasks.fileify(v)
		except:
		    pass
        else:
            for slug in args:
                p = Project.objects.get(slug=slug)
                print "Indexing %s" % p
                tasks.fileify(p)
