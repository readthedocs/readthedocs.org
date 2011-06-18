import os
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run

class Builder(HtmlBuilder):

    def build(self, version):
        project = version.project
        os.chdir(version.project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b dirhtml . _build/html' % project.venv_bin(version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b dirhtml . _build/html"
        build_results = run(build_command)
        return build_results
