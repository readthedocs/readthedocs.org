# -*- coding: utf-8 -*-

"""We define custom Django signals to trigger before executing searches."""
import django.dispatch
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_elasticsearch_dsl.apps import DEDConfig
from django_elasticsearch_dsl.registries import registry

from readthedocs.projects.models import HTMLFile, Project
from readthedocs.projects.signals import bulk_post_create, bulk_post_delete
from readthedocs.search.documents import PageDocument, ProjectDocument
from readthedocs.search.tasks import index_objects_to_es


before_project_search = django.dispatch.Signal(providing_args=['body'])
before_file_search = django.dispatch.Signal(providing_args=['body'])
before_section_search = django.dispatch.Signal(providing_args=['body'])


@receiver(bulk_post_create, sender=HTMLFile)
def index_html_file(instance_list, **_):
    kwargs = {
        'app_label': HTMLFile._meta.app_label,
        'model_name': HTMLFile.__name__,
        'document_class': str(PageDocument),
        'index_name': None,  # No need to change the index name
        'objects_id': [obj.id for obj in instance_list],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es(**kwargs)


@receiver(bulk_post_delete, sender=HTMLFile)
def remove_html_file(instance_list, **_):
    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        registry.delete(instance_list)


@receiver(post_save, sender=Project)
def index_project(instance, *args, **kwargs):
    kwargs = {
        'app_label': Project._meta.app_label,
        'model_name': Project.__name__,
        'document_class': str(ProjectDocument),
        'index_name': None,  # No need to change the index name
        'objects_id': [instance.id],
    }

    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        index_objects_to_es.delay(**kwargs)


@receiver(pre_delete, sender=Project)
def remove_project(instance, *args, **kwargs):
    # Do not index if autosync is disabled globally
    if DEDConfig.autosync_enabled():
        registry.delete(instance)
