import os
import logging

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run

log = logging.getLogger(__name__)

class Builder(BaseBuilder):
    """
    Mkdocs builder
    """
    type = 'mkdocs'

    def __init__(self, *args, **kwargs):
        super(Builder, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(self.version.project.checkout_path(self.version.slug), 'site')

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.checkout_path(self.version.slug))
        if project.use_virtualenv:
            build_command = "%s build --theme=readthedocs" % (
                project.venv_bin(version=self.version.slug,
                                 bin='mkdocs')
                )
        else:
            build_command = "mkdocs build --theme=readthedocs"
        results = run(build_command, shell=True)
        return results
