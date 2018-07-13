import logging

from django.apps import apps
from django_elasticsearch_dsl.registries import registry

from readthedocs.worker import app

log = logging.getLogger(__name__)


def _get_index(indices, index_name):
    for index in indices:
        if str(index) == index_name:
            return index


def _get_document(model, document_class):
    documents = registry.get_documents(models=[model])

    for document in documents:
        if str(document) == document_class:
            return document


@app.task(queue='web')
def create_new_es_index_task(app_label, model_name, old_index_name, new_index_name):
    model = apps.get_model(app_label, model_name)
    indices = registry.get_indices(models=[model])
    old_index = _get_index(indices=indices, index_name=old_index_name)
    new_index = old_index.clone(name=new_index_name)
    new_index.create()


@app.task(queue='web')
def switch_es_index_task(app_label, model_name, old_index_name, new_index_name):
    model = apps.get_model(app_label, model_name)
    indices = registry.get_indices(models=[model])
    old_index = _get_index(indices=indices, index_name=old_index_name)

    new_index = old_index.clone(name=new_index_name)

    if old_index.exists():
        # Alias can not be used to delete an index.
        # https://www.elastic.co/guide/en/elasticsearch/reference/6.0/indices-delete-index.html
        # So get the index actual name to delete it
        old_index_info = old_index.get()
        # The info is a dictionary and the key is the actual name of the index
        old_index_name = old_index_info.keys()[0]
        old_index.connection.indices.delete(index=old_index_name)

    new_index.put_alias(name=old_index_name)


@app.task(queue='web')
def index_objects_to_es_task(app_label, model_name, document_class, index_name, objects_id):
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)

    # Use queryset from model as the ids are specific
    queryset = model.objects.all().filter(id__in=objects_id).iterator()
    log.info("Indexing model: {}, id:'{}'".format(model.__name__, objects_id))
    document().update(queryset, index_name=index_name)


@app.task(queue='web')
def index_missing_objects_task(app_label, model_name, document_class, indexed_instance_ids):
    """
    Task to insure that none of the object is missed from indexing.

    The object ids are sent to task for indexing.
    But in the meantime, new objects can be created/deleted in database
    and they will not be in the tasks.
    This task will index all the objects excluding the ones which have got indexed already
    """
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)
    queryset = document().get_queryset().exclude(id__in=indexed_instance_ids)
    document().update(queryset.iterator())

    log.info("Indexed {} missing objects from model: {}'".format(queryset.count(), model.__name__))

    # TODO: Figure out how to remove the objects from ES index that has been deleted
