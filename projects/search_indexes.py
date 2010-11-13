import datetime
import os
import codecs

from haystack.indexes import *
from haystack import site
from projects.models import File, ImportedFile, Project
from projects import constants

class ProjectIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')
    title = CharField(model_attr='name')
    description = CharField(model_attr='description')
    repo_type = CharField(model_attr='repo_type')

    def get_queryset(self):
        return Project.objects.filter(status=constants.LIVE_STATUS)


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
        try:
            content = codecs.open(to_read, encoding="utf-8", mode='r').read()
            return content
        except IOError:
            print "%s not found" % full_path
            #obj.delete()

    def get_queryset(self):
        return ImportedFile.objects.filter(project__status=constants.LIVE_STATUS)

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
site.register(Project, ProjectIndex)
