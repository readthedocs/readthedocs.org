import logging
import fileinput
import json
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from projects import tasks
from tastyapi import api

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Trigger build for project version"""

    args = '<files>'

    def handle(self, files=None, *args, **options):
        if files is None:
            files = '-'

        def _return_json(output):
            return json.dumps(output)

        try:
            fh = fileinput.FileInput(files)
            input_data = ''.join([line for line in fh])
            version_data = json.loads(input_data)
            version = tasks.make_api_version(version_data)
            log.info('Building %s', version)
            output = _return_json(tasks.docker_build(version))
        except Exception as e:
            output = _return_json(
                {'doc_builder': (-1, '', '{0}: {1}'.format(type(e).__name__,
                                                           str(e)))})
        finally:
            print(output)
