"""Rebuild documentation for all projects"""

from __future__ import absolute_import
from __future__ import print_function
from glob import glob
import os
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader as template_loader

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        doc_index = {}

        os.chdir(settings.DOCROOT)
        for directory in glob("*"):
            doc_index[directory] = []
            path = os.path.join(directory, 'rtd-builds')
            for version in glob(os.path.join(path, "*")):
                v = version.replace(path + '/', '')
                doc_index[directory].append(v)

        context = {
            'doc_index': doc_index,
            'MEDIA_URL': settings.MEDIA_URL,
        }
        html = template_loader.get_template('archive/index.html').render(context)
        print(html)
