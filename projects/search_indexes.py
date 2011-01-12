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

class FileIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='project__user', faceted=True)
    project = CharField(model_attr='project__name', faceted=True)
    title = CharField(model_attr='heading')

#Should prob make a common subclass for this and FileIndex
class ImportedFileIndex(SearchIndex):
    text = CharField(document=True)
    author = CharField(model_attr='project__user', faceted=True)
    project = CharField(model_attr='project__name', faceted=True)
    title = CharField(model_attr='name')

    def prepare_text(self, obj):
        try:
            full_path = obj.project.full_html_path
            to_read = os.path.join(full_path, obj.path.lstrip('/'))
            content = codecs.open(to_read, encoding="utf-8", mode='r').read()
            return content
        except (AttributeError, IOError):
            print "%s not found" % full_path
            #obj.delete()

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
site.register(Project, ProjectIndex)
