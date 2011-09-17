# -*- coding: utf-8-*-

import os
import codecs
import BeautifulSoup

from django.utils.html import strip_tags
from haystack.indexes import *
from haystack import site
from projects.models import File, ImportedFile, Project

from celery_haystack.indexes import CelerySearchIndex

class ProjectIndex(CelerySearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField()
    title = CharField(model_attr='name')
    description = CharField(model_attr='description')
    repo_type = CharField(model_attr='repo_type')

    def prepare_author(self, obj):
        return obj.users.all()[0]

class FileIndex(CelerySearchIndex):
    text = CharField(document=True, use_template=True)
    author = CharField()
    project = CharField(model_attr='project__name', faceted=True)
    title = CharField(model_attr='heading')

    def prepare_author(self, obj):
        return obj.project.users.all()[0]

#Should prob make a common subclass for this and FileIndex
class ImportedFileIndex(CelerySearchIndex):
    text = CharField(document=True)
    author = CharField()
    project = CharField(model_attr='project__name', faceted=True)
    title = CharField(model_attr='name')

    def prepare_author(self, obj):
        return obj.project.users.all()[0]

    def prepare_text(self, obj):
        """
        Prepare the text of the html file.
        This only works on machines that have the html
        files for the projects checked out.
        """
        try:
            full_path = obj.project.rtd_build_path()
            to_read = os.path.join(full_path, obj.path.lstrip('/'))
            content = codecs.open(to_read, encoding="utf-8", mode='r').read()
            bs = BeautifulSoup.BeautifulSoup(content)
            soup = bs.find("div", {"class": "document"})
            return strip_tags(soup).replace(u'¶', '')
        except (AttributeError, IOError) as e:
            if 'full_path' in locals():
                print "%s not found: %s " % (full_path, e)
            #obj.delete()

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
site.register(Project, ProjectIndex)
