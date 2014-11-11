# -*- coding: utf-8 -*-

import codecs
import os

from django.conf import settings
from django.utils.html import strip_tags

#from haystack import site
from haystack import indexes
from haystack.fields import CharField

from projects import constants
from projects.models import ImportedFile, Project

import logging
log = logging.getLogger(__name__)


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = CharField(document=True, use_template=True)
    author = CharField()
    title = CharField(model_attr='name')
    description = CharField(model_attr='description')
    repo_type = CharField(model_attr='repo_type')
    absolute_url = CharField()

    def prepare_author(self, obj):
        return obj.users.all()[0]

    def prepare_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_model(self):
        return Project

    def index_queryset(self):
        "Used when the entire index for model is updated."
        return self.get_model().objects.public()


#Should prob make a common subclass for this and FileIndex
class ImportedFileIndex(indexes.SearchIndex, indexes.Indexable):
    text = CharField(document=True)
    author = CharField()
    project = CharField(model_attr='project__name', faceted=True)
    version = CharField(model_attr='version__slug', faceted=True)
    title = CharField(model_attr='name')
    absolute_url = CharField()

    def prepare_author(self, obj):
        return obj.project.users.all()[0]

    def prepare_title(self, obj):
        return obj.name.replace('.html', '').replace('_', ' ').title()

    def prepare_absolute_url(self, obj):
        return obj.get_absolute_url()

    def prepare_text(self, obj):
        """
        Prepare the text of the html file.
        This only works on machines that have the html
        files for the projects checked out.
        """
        #Import this here to hopefully fix tests for now.
        from pyquery import PyQuery
        full_path = obj.project.rtd_build_path()
        file_path = os.path.join(full_path, obj.path.lstrip('/'))
        try:
            with codecs.open(file_path, encoding='utf-8', mode='r') as f:
                content = f.read()
        except IOError as e:
            log.info('(Search Index) Unable to index file: %s, error :%s' % (file_path, e))
            return
        log.debug('(Search Index) Indexing %s:%s' % (obj.project, obj.path))
        DOCUMENT_PYQUERY_PATH = getattr(settings, 'DOCUMENT_PYQUERY_PATH',
                                        'div.document')
        try:
            to_index = strip_tags(PyQuery(content)(
                DOCUMENT_PYQUERY_PATH).html()).replace(u'¶', '')
        except ValueError:
            #Pyquery returns ValueError if div.document doesn't exist.
            return
        if not to_index:
            log.info('(Search Index) Unable to index file: %s:%s, empty file' % (obj.project,
                                                                  file_path))
        else:
            log.debug('(Search Index) %s:%s length: %s' % (obj.project, file_path,
                                            len(to_index)))
        return to_index

    def get_model(self):
        return ImportedFile

    def index_queryset(self):
        "Used when the entire index for model is updated."
        return (self.get_model().objects
                .filter(project__privacy_level=constants.PUBLIC))
