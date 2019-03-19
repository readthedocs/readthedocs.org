# -*- coding: utf-8 -*-

"""We define custom Django signals to trigger before executing searches."""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_elasticsearch_dsl.apps import DEDConfig
from django_elasticsearch_dsl.registries import registry

from readthedocs.projects.models import Project
from readthedocs.projects.signals import bulk_post_create, bulk_post_delete
from readthedocs.search.tasks import delete_objects_in_es, index_objects_to_es


@receiver(bulk_post_create)
def index_indexed_file(sender, instance_list, **_):
    """Handle indexing from the build process."""
    model = sender
    document = registry.get_documents(models=[model])[0]
    kwargs = {
        'app_label': model._meta.app_label,
        'model_name': model.__name__,
        'document_class': str(document),
        'objects_id': [obj.id for obj in instance_list],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es(**kwargs)


@receiver(bulk_post_delete)
def remove_indexed_file(sender, instance_list, **_):
    """Remove deleted files from the build process."""
    model = sender
    document = registry.get_documents(models=[model])[0]

    kwargs = {
        'app_label': model._meta.app_label,
        'model_name': model.__name__,
        'document_class': str(document),
        'objects_id': [obj.id for obj in instance_list],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        delete_objects_in_es(**kwargs)


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
