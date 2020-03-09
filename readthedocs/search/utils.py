"""Utilities related to reading and generating indexable search content."""

import logging
from operator import attrgetter

from django.shortcuts import get_object_or_404
from django_elasticsearch_dsl.apps import DEDConfig
from django_elasticsearch_dsl.registries import registry

from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.documents import PageDocument


log = logging.getLogger(__name__)


def index_new_files(model, version, build):
    """Index new files from the version into the search index."""

    if not DEDConfig.autosync_enabled():
        log.info(
            'Autosync disabled, skipping indexing into the search index for: %s:%s',
            version.project.slug,
            version.slug,
        )
        return

    try:
        document = list(registry.get_documents(models=[model]))[0]
        doc_obj = document()
        queryset = (
            doc_obj.get_queryset()
            .filter(project=version.project, version=version, build=build)
        )
        log.info(
            'Indexing new objecst into search index for: %s:%s',
            version.project.slug,
            version.slug,
        )
        doc_obj.update(queryset.iterator())
    except Exception:
        log.exception('Unable to index a subset of files. Continuing.')


def remove_indexed_files(model, project_slug, version_slug=None, build_id=None):
    """
    Remove files from `version_slug` of `project_slug` from the search index.

    :param model: Class of the model to be deleted.
    :param project_slug: Project slug.
    :param version_slug: Version slug. If isn't given,
                    all index from `project` are deleted.
    :param build_id: Build id. If isn't given, all index from `version` are deleted.
    """

    if not DEDConfig.autosync_enabled():
        log.info(
            'Autosync disabled, skipping removal from the search index for: %s:%s',
            project_slug,
            version_slug,
        )
        return

    try:
        document = list(registry.get_documents(models=[model]))[0]
        log.info(
            'Deleting old files from search index for: %s:%s',
            project_slug,
            version_slug,
        )
        documents = (
            document().search()
            .filter('term', project=project_slug)
        )
        if version_slug:
            documents = documents.filter('term', version=version_slug)
        if build_id:
            documents = documents.exclude('term', build=build_id)
        documents.delete()
    except Exception:
        log.exception('Unable to delete a subset of files. Continuing.')


def _get_index(indices, index_name):
    """
    Get Index from all the indices.

    :param indices: DED indices list
    :param index_name: Name of the index
    :return: DED Index
    """
    for index in indices:
        if str(index) == index_name:
            return index


def _get_document(model, document_class):
    """
    Get DED document class object from the model and name of document class.

    :param model: The model class to find the document
    :param document_class: the name of the document class.
    :return: DED DocType object
    """
    documents = registry.get_documents(models=[model])

    for document in documents:
        if str(document) == document_class:
            return document


def _indexing_helper(html_objs_qs, wipe=False):
    """
    Helper function for reindexing and wiping indexes of projects and versions.

    If ``wipe`` is set to False, html_objs are deleted from the ES index,
    else, html_objs are indexed.
    """
    from readthedocs.search.tasks import index_objects_to_es, delete_objects_in_es

    if html_objs_qs:
        obj_ids = []
        for html_objs in html_objs_qs:
            obj_ids.extend([obj.id for obj in html_objs])

        # removing redundant ids if exists.
        obj_ids = list(set(obj_ids))

        if obj_ids:
            kwargs = {
                'app_label': HTMLFile._meta.app_label,
                'model_name': HTMLFile.__name__,
                'document_class': str(PageDocument),
                'objects_id': obj_ids,
            }

            if not wipe:
                index_objects_to_es.delay(**kwargs)
            else:
                delete_objects_in_es.delay(**kwargs)


def _get_sorted_results(results, source_key='_source'):
    """Sort results according to their score and returns results as list."""
    sorted_results = [
        {
            'type': hit._nested.field,
            source_key: hit._source.to_dict(),
            'highlight': hit.highlight.to_dict() if hasattr(hit, 'highlight') else {}
        }
        for hit in sorted(results, key=attrgetter('_score'), reverse=True)
    ]

    return sorted_results
