import os
import logging

from doc_builder.base import BaseBuilder, restoring_chdir
from projects.utils import run

log = logging.getLogger(__name__)

class Builder(BaseBuilder):
    """
    Ascii Doctor builder
    """
    type = 'asciidoc'

    def __init__(self, *args, **kwargs):
        super(BaseBuilder, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(self.version.project.checkout_path(self.version.slug), 'site')

    @restoring_chdir
    def build(self, **kwargs):
        project = self.version.project
        os.chdir(project.checkout_path(self.version.slug))
        results = {}
        if project.use_virtualenv:
            build_command = "%s build " % (
                project.venv_bin(version=self.version.slug,
                                 bin='asciidoctor')
                )
        else:
            build_command = "asciidoctor build"
        results['html'] = run(build_command, shell=True)
        return results
