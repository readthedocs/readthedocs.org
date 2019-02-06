# -*- coding: utf-8 -*-

"""Utilities related to reading and generating indexable search content."""

import logging

from django.shortcuts import get_object_or_404
from django_elasticsearch_dsl.registries import registry

from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


# TODO: Rewrite all the views using this in Class Based View,
# and move this function to a mixin
def get_project_list_or_404(project_slug, user):
    """Return list of project and its subprojects."""
    queryset = Project.objects.public(user).only('slug')

    project = get_object_or_404(queryset, slug=project_slug)
    subprojects = queryset.filter(superprojects__parent_id=project.id)

    project_list = list(subprojects) + [project]
    return project_list


def get_chunk(total, chunk_size):
    """Yield successive `chunk_size` chunks."""
    # Based on https://stackoverflow.com/a/312464
    # licensed under cc by-sa 3.0
    for i in range(0, total, chunk_size):
        yield (i, i + chunk_size)


def _get_index(indices, index_name):
    """
    Get Index from all the indices

    :param indices: DED indices list
    :param index_name: Name of the index
    :return: DED Index
    """
    for index in indices:
        if str(index) == index_name:
            return index


def _get_document(model, document_class):
    """
    Get DED document class object from the model and name of document class

    :param model: The model class to find the document
    :param document_class: the name of the document class.
    :return: DED DocType object
    """
    documents = registry.get_documents(models=[model])

    for document in documents:
        if str(document) == document_class:
            return document
