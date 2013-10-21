from glob import glob
import logging
import os
import shutil
import tarfile

from django.conf import settings
from django.template import Template, Context

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run
from core.utils import copy_file_to_app_servers


log = logging.getLogger(__name__)

FEED_TEMPLATE = """<entry>
    <version>{{ version.slug }}</version>
    <url>{{ media_url_prefix }}{{ version.project.get_dash_url }}</url>
</entry>
"""

class Builder(HtmlBuilder):

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.conf_dir(self.version.slug))
        if os.path.exists('_build/dash'):
            shutil.rmtree('_build/dash')
        os.makedirs('_build/dash')
        dash_build_command = ("doc2dash --name=\"%s\" --force "
                              "--destination=_build/dash _build/html"
                              % project.name)
        dash_build_results = run(dash_build_command, shell=True)
        self._zip_dash()
        self._write_feed()
        return dash_build_results

    def _write_feed(self):
        if settings.MEDIA_URL.startswith('//'):
            media_url_prefix = 'http:'
        else:
            media_url_prefix = ''
        context = Context({
            'version': self.version,
            'media_url_prefix': media_url_prefix,
        })
        feed_content = Template(FEED_TEMPLATE).render(context)
        to_file = self.version.project.get_dash_feed_path(self.version.slug)
        to_path = self.version.project.checkout_path(self.version.slug)
        to_file = os.path.join(to_path, '%s.xml' % self.version.project.doc_name)
        if not os.path.exists(to_path):
            os.makedirs(to_path)
        with open(to_file, 'w') as feed_file:
            feed_file.write(feed_content)

    @restoring_chdir
    def _zip_dash(self, **kwargs):
        from_path = self.version.project.full_dash_path(self.version.slug)
        to_path = self.version.project.checkout_path(self.version.slug)
        to_file = os.path.join(to_path,
                               '%s.tgz' % self.version.project.doc_name)

        log.info("Creating dash tarball from %s at %s" %
                 (from_path, to_file))
        # Create a <slug>.tgz file containing all files in file_path
        os.chdir(from_path)
        archive = tarfile.open(to_file, "w:gz")
        # archive = zipfile.ZipFile(to_file, 'w')
        for root, subfolders, files in os.walk('.'):
            for file in files:
                to_write = os.path.join(root, file)
                archive.add(to_write)
        archive.close()
        return to_file

    def move(self, **kwargs):
        project = self.version.project
        outputted_path = self.version.project.checkout_path(self.version.slug)
        to_path = os.path.join(settings.MEDIA_ROOT,
                               'dash',
                               project.slug,
                               self.version.slug)
        
        from_globs = glob(os.path.join(outputted_path, "*.tgz"))
        if from_globs:
            from_file = from_globs[0]
            to_file = os.path.join(to_path, "%s.tgz" % project.doc_name)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_file_to_app_servers(from_file, to_file)
            else:
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                run('mv -f %s %s' % (from_file, to_file))

        xml_globs = glob(os.path.join(outputted_path, "*.xml"))
        if xml_globs:
            from_file = xml_globs[0]
            to_file = os.path.join(to_path, "%s.xml" % project.doc_name)
            if getattr(settings, "MULTIPLE_APP_SERVERS", None):
                copy_file_to_app_servers(from_file, to_file)
            else:
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                run('mv -f %s %s' % (from_file, to_file))
