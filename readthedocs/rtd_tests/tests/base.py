import os
import shutil
import logging

from django.conf import settings
from django.test import TestCase

log = logging.getLogger(__name__)


class RTDTestCase(TestCase):
    def setUp(self):
        self.cwd = os.path.dirname(__file__)
        self.build_dir = os.path.join(self.cwd, 'builds')
        log.info("build dir: %s" % self.build_dir)
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        settings.DOCROOT = self.build_dir

    def tearDown(self):
        shutil.rmtree(self.build_dir)
