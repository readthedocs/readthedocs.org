import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from builds.models import Version
from search import parse_json
from restapi.utils import index_search_request

log = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    dest='project',
                    default='',
                    help='Project to index'),
    )

    def handle(self, *args, **options):
        '''
        Build/index all versions or a single project's version
        '''
        project = options['project']

        if project:
            queryset = Version.objects.public(project__slug=project)
            log.info("Building all versions for %s" % project)
        elif getattr(settings, 'INDEX_ONLY_LATEST', True):
            queryset = Version.objects.public().filter(slug='latest')
        else:
            queryset = Version.objects.public()
        for version in queryset:
            log.info("Reindexing %s" % version)
            try:
                page_list = parse_json.process_all_json_files(version, build_dir=False)
                index_search_request(version=version, page_list=page_list)
            except Exception:
                log.error('Build failed for %s' % version, exc_info=True)
