import zipfile
import logging
import os

from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run

log = logging.getLogger(__name__)


class Builder(HtmlBuilder):
    
    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        results = {}
        if project.use_virtualenv:
            build_command = '%s -b readthedocssinglehtml -D language=%s . _build/html' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocssinglehtml . _build/html" % project.language
        results['singlehtml'] = run(build_command)
        #self._zip_html()
        if 'no targets are out of date.' in results['singlehtml'][1]:
            self._changed = False
        return results

class LocalMediaBuilder(HtmlBuilder):

    def from_path(self):
         return os.path.join(self.version.project.conf_dir(self.version.slug), "_build", "localmedia")

    def to_file(self):
        to_path = self.version.project.checkout_path(self.version.slug)
        return os.path.join(to_path, '%s.zip' % self.version.project.slug)
    
    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        results = {}
        if project.use_virtualenv:
            build_command = '%s -b readthedocssinglehtmllocalmedia -D language=%s . _build/localmedia' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocssinglehtmllocalmedia . _build/localmedia" % project.language
        results['localmedia'] = run(build_command)
        self._zip_html()
        if 'no targets are out of date.' in results['localmedia'][1]:
            self._changed = False
        return results

    @restoring_chdir
    def _zip_html(self, **kwargs):
        from_path = self.from_path()
        to_file = self.to_file()

        log.info("Creating zip file from %s" % from_path)
        # Create a <slug>.zip file containing all files in file_path
        os.chdir(from_path)
        archive = zipfile.ZipFile(to_file, 'w')
        for root, subfolders, files in os.walk('.'):
            for file in files:
                to_write = os.path.join(root, file)
                archive.write(
                    filename=to_write,
                    arcname=os.path.join("%s-%s" % (self.version.project.slug,
                                                    self.version.slug),
                                         to_write)
                )
        archive.close()
        return to_file
