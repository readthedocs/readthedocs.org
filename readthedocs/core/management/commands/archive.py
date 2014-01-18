from glob import glob
import os
import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, loader as template_loader

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """Custom management command to rebuild documentation for all projects on
    the site. Invoked via ``./manage.py update_repos``.
    """

    def handle(self, *args, **options):
		doc_index = {}

		os.chdir(settings.DOCROOT)
		for directory in glob("*"):
			doc_index[directory] = []
			path = os.path.join(directory, 'rtd-builds')
			for version in glob(os.path.join(path, "*")):
				v = version.replace(path + '/', '')
				doc_index[directory].append(v)

		context = Context({
			'doc_index': doc_index,
		})
		html = template_loader.get_template('archive/index.html').render(context)
		print html
