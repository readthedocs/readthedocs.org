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
        if project.use_virtualenv:
            build_command = '%s -b readthedocssinglehtml -D language=%s . _build/singlehtml' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocssinglehtml . _build/singlehtml" % project.language
        build_results = run(build_command)
        #self._zip_html()
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

class LocalMediaBuilder(HtmlBuilder):
    
    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(self.version.project.conf_dir(self.version.slug))
        if project.use_virtualenv:
            build_command = '%s -b readthedocssinglehtmllocalmedia -D language=%s . _build/singlehtml' % (project.venv_bin(
                version=self.version.slug, bin='sphinx-build'), project.language)
        else:
            build_command = "sphinx-build -D language=%s -b readthedocssinglehtmllocalmedia . _build/singlehtml" % project.language
        build_results = run(build_command)
        self._zip_html()
        if 'no targets are out of date.' in build_results[1]:
            self._changed = False
        return build_results

    @restoring_chdir
    def _zip_html(self, **kwargs):
        from_path = self.version.project.full_singlehtml_path(self.version.slug)
        to_path = self.version.project.checkout_path(self.version.slug)
        to_file = os.path.join(to_path, '%s.zip' % self.version.project.slug)

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
