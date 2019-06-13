"""We define custom Django signals to trigger before executing searches."""
import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_elasticsearch_dsl.apps import DEDConfig
from django_elasticsearch_dsl.registries import registry

from readthedocs.projects.models import Project
from readthedocs.search.tasks import delete_objects_in_es, index_objects_to_es


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


def remove_indexed_files(model, version, build):
    """
    Remove files from the version from the search index.

    This excludes files from the current build.
    """

    if not DEDConfig.autosync_enabled():
        log.info(
            'Autosync disabled, skipping removal from the search index for: %s:%s',
            version.project.slug,
            version.slug,
        )
        return

    try:
        document = list(registry.get_documents(models=[model]))[0]
        log.info(
            'Deleting old files from search index for: %s:%s',
            version.project.slug,
            version.slug,
        )
        (
            document().search()
            .filter('term', project=version.project.slug)
            .filter('term', version=version.slug)
            .exclude('term', build=build)
            .delete()
        )
    except Exception:
        log.exception('Unable to delete a subset of files. Continuing.')


@receiver(post_save, sender=Project)
def index_project_save(instance, *args, **kwargs):
    """
    Save a Project instance based on the post_save signal.post_save.

    This uses Celery to do it async, replacing how django-elasticsearch-dsl does
    it.
    """
    from readthedocs.search.documents import ProjectDocument
    kwargs = {
        'app_label': Project._meta.app_label,
        'model_name': Project.__name__,
        'document_class': str(ProjectDocument),
        'objects_id': [instance.id],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es.delay(**kwargs)


@receiver(pre_delete, sender=Project)
def remove_project_delete(instance, *args, **kwargs):
    from readthedocs.search.documents import ProjectDocument
    kwargs = {
        'app_label': Project._meta.app_label,
        'model_name': Project.__name__,
        'document_class': str(ProjectDocument),
        'objects_id': [instance.id],
    }

    # Don't `delay` this because the objects will be deleted already
    if DEDConfig.autosync_enabled():
        delete_objects_in_es(**kwargs)
