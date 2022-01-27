"""We define custom Django signals to trigger before executing searches."""
import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_elasticsearch_dsl.apps import DEDConfig

from readthedocs.projects.models import Project
from readthedocs.search.tasks import delete_objects_in_es, index_objects_to_es

log = logging.getLogger(__name__)


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
    else:
        log.info('Skipping indexing')


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
    else:
        log.info('Skipping indexing')
