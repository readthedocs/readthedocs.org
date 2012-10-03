import logging

from django.core.management.base import BaseCommand
from projects import tasks
from projects.models import Project, ImportedFile
from builds.models import Version

log = logging.getLogger(__name__)

class Command(BaseCommand):

    help = '''\
Delete and re-create ImportedFile objects for all latest Versions, such
that they can be added to the search index. This is accomplished by walking the 
filesystem for each project.
'''

    def handle(self, *args, **kwargs):
        '''
        Build/index all versions or a single project's version
        '''
        # Delete all existing as a cleanup for any deleted projects.
        ImportedFile.objects.all().delete()
        for v in Version.objects.filter(slug='latest'):
            log.info("Building files for %s" % v)
            try:
                tasks.fileify(v)
            except Exception, e:
                log.error('Build failed for %s' % v, exc_info=True)
