# -*- coding: utf-8 -*-

"""We define custom Django signals to trigger before executing searches."""
import django.dispatch
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_elasticsearch_dsl.apps import DEDConfig

from readthedocs.projects.models import HTMLFile, Project
from readthedocs.projects.signals import bulk_post_create, bulk_post_delete
from readthedocs.search.tasks import delete_objects_in_es, index_objects_to_es

before_domain_search = django.dispatch.Signal(providing_args=['user', 'search'])
before_file_search = django.dispatch.Signal(providing_args=['user', 'search'])
before_project_search = django.dispatch.Signal(providing_args=['user', 'search'])


@receiver(bulk_post_create, sender=HTMLFile)
def index_html_file(instance_list, **_):
    """Handle indexing from the build process."""
    from readthedocs.search.documents import PageDocument
    kwargs = {
        'app_label': HTMLFile._meta.app_label,
        'model_name': HTMLFile.__name__,
        'document_class': str(PageDocument),
        'objects_id': [obj.id for obj in instance_list],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es(**kwargs)


@receiver(bulk_post_delete, sender=HTMLFile)
def remove_html_file(instance_list, **_):
    """Remove deleted files from the build process."""
    from readthedocs.search.documents import PageDocument
    kwargs = {
        'app_label': HTMLFile._meta.app_label,
        'model_name': HTMLFile.__name__,
        'document_class': str(PageDocument),
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

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        delete_objects_in_es.delay(**kwargs)


@receiver(post_save, sender=HTMLFile)
def index_html_file_save(instance, *args, **kwargs):
    """
    Save a HTMLFile instance based on the post_save signal.post_save.

    This uses Celery to do it async, replacing how django-elasticsearch-dsl does
    it.
    """
    from readthedocs.search.documents import PageDocument
    kwargs = {
        'app_label': HTMLFile._meta.app_label,
        'model_name': HTMLFile.__name__,
        'document_class': str(PageDocument),
        'objects_id': [instance.id],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es.delay(**kwargs)


@receiver(pre_delete, sender=HTMLFile)
def remove_html_file_delete(instance, *args, **kwargs):
    from readthedocs.search.documents import PageDocument

    kwargs = {
        'app_label': HTMLFile._meta.app_label,
        'model_name': HTMLFile.__name__,
        'document_class': str(PageDocument),
        'objects_id': [instance.id],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        delete_objects_in_es.delay(**kwargs)
