import datetime
import os
from haystack.indexes import *
from haystack import site
from projects.models import File, ImportedFile
from projects import constants

class FileIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='project__user')
    project = CharField(model_attr='project__name')
    title = CharField(model_attr='heading')

    def get_queryset(self):
        return File.objects.filter(project__status=constants.LIVE_STATUS)

class ImportedFileIndex(SearchIndex):
    text = CharField(document=True)
    author = CharField(model_attr='project__user')
    project = CharField(model_attr='project__name')
    title = CharField(model_attr='name')

    def prepare_text(self, obj):
        full_path = obj.project.full_html_path
        to_read = os.path.join(full_path, obj.path.lstrip('/'))
        content = open(to_read, 'r').read()
        return content

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
