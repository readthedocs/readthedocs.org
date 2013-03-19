import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings


from projects import tasks
from builds.models import Version

log = logging.getLogger(__name__)

class Command(BaseCommand):

    help = '''\
Delete and re-create ImportedFile objects for all latest Versions, such
that they can be added to the search index. This is accomplished by walking the
filesystem for each project.
'''

    option_list = BaseCommand.option_list + (
        make_option('-p',
            dest='project',
            default='',
            help='Project to index'
        ),
    )


    def handle(self, *args, **options):
        '''
        Build/index all versions or a single project's version
        '''
        # Delete all existing as a cleanup for any deleted projects.
        #ImportedFile.objects.all().delete()
        project = options['project']

        if project:
            queryset = Version.objects.public(project__slug=project)
            log.info("Building all versions for %s" % project)
        elif getattr(settings, 'INDEX_ONLY_LATEST', True):
            queryset = Version.objects.filter(slug='latst')
        else:
            queryset = Version.objects.public()
        for v in queryset:
            log.info("Building files for %s" % v)
            try:
                tasks.fileify(v.pk)
            except Exception:
                log.error('Build failed for %s' % v, exc_info=True)
