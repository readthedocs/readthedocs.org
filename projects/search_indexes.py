import datetime
from haystack.indexes import *
from haystack import site
from projects.models import File, ImportedFile
from projects import constants

class FileIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='project__user')
    project = CharField(model_attr='project__name')
    name = CharField(model_attr='heading')

    def get_queryset(self):
        return File.objects.filter(project__status=constants.LIVE_STATUS)

class ImportedFileIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='project__user')
    project = CharField(model_attr='project__name')
    name = CharField(model_attr='name')

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
