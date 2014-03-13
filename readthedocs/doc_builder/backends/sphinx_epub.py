from glob import glob
import os
from doc_builder.base import restoring_chdir
from doc_builder.backends.sphinx import Builder as HtmlBuilder
from projects.utils import run
from core.utils import copy_file_to_app_servers

from django.conf import settings


class Builder(HtmlBuilder):

    sphinx_builder = 'epub'
    sphinx_build_dir = '_build/epub'
    results_name = 'epub'
    type = 'sphinx_epub'

    def __init__(self, *args, **kwargs):
        super(Builder).__init__(*args, **kwargs)
        prod_path = os.path.join(settings.MEDIA_ROOT, 'epub', project.slug, self.version.slug)

