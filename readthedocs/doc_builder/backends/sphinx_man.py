import os
from doc_builder.backends.sphinx import Builder as ManpageBuilder
from projects.utils import safe_write, run


class Builder(ManpageBuilder):

    def build(self, version):
        project = version.project
        os.chdir(version.project.conf_dir(version.slug))
        if project.use_virtualenv and project.whitelisted:
            build_command = '%s -b man . _build/man' % project.venv_bin(
                version=version.slug, bin='sphinx-build')
        else:
            build_command = "sphinx-build -b man . _build/man"
        build_results = run(build_command)
        return build_results
