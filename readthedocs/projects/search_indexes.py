# -*- coding: utf-8-*-

import codecs
import os

from django.utils.html import strip_tags

from haystack import site
from haystack.indexes import *

from celery_haystack.indexes import CelerySearchIndex

from pyquery import PyQuery

from projects.models import File, ImportedFile, Project

import logging
log = logging.getLogger(__name__)

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
        full_path = obj.project.rtd_build_path()
        file_path = os.path.join(full_path, obj.path.lstrip('/'))
        try:
            with codecs.open(file_path, encoding='utf-8', mode='r') as f:
                content = f.read()
        except (AttributeError, IOError) as e:
            log.info('Unable to index file: %s' % file_path)
        log.debug('Indexing %s' % obj.slug)
        to_index = strip_tags(PyQuery(content)("div.document").html()).replace(u'¶', '')
        return to_index

site.register(File, FileIndex)
site.register(ImportedFile, ImportedFileIndex)
site.register(Project, ProjectIndex)
