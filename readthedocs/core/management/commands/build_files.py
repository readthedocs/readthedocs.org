import logging

from django.core.management.base import BaseCommand
from django.conf import settings


from projects import tasks
from projects.models import ImportedFile
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
        if getattr(settings, 'INDEX_ONLY_LATEST', False):
            queryset = Version.objects.filter(slug='latst')
        else:
            queryset = Version.objects.public()
        for v in queryset:
            log.info("Building files for %s" % v)
            try:
                tasks.fileify(v)
            except Exception:
                log.error('Build failed for %s' % v, exc_info=True)
