import logging

from django.apps import apps
from django.utils import timezone
from django_elasticsearch_dsl.registries import registry

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.models import SearchQuery
from readthedocs.worker import app
from .models import SearchQuery
from .utils import _get_index, _get_document

log = logging.getLogger(__name__)


@app.task(queue='web')
def index_objects_to_es(
    app_label, model_name, document_class, index_name=None, chunk=None, objects_id=None
):

    if chunk and objects_id:
        raise ValueError('You can not pass both chunk and objects_id.')

    if not (chunk or objects_id):
        raise ValueError('You must pass a chunk or objects_id.')

    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)
    doc_obj = document()

    # WARNING: This must use the exact same queryset as from where we get the ID's
    # There is a chance there is a race condition here as the ID's may change as the task runs,
    # so we need to think through this a bit more and probably pass explicit ID's,
    # but there are performance issues with that on large model sets
    queryset = doc_obj.get_queryset()
    if chunk:
        # Chunk is a tuple with start and end index of queryset
        start = chunk[0]
        end = chunk[1]
        queryset = queryset[start:end]
    elif objects_id:
        queryset = queryset.filter(id__in=objects_id)

    if index_name:
        # Hack the index name temporarily for reindexing tasks
        old_index_name = document._doc_type.index
        document._doc_type.index = index_name
        log.info('Replacing index name %s with %s', old_index_name, index_name)

    log.info("Indexing model: %s, '%s' objects", model.__name__, queryset.count())
    doc_obj.update(queryset.iterator())

    if index_name:
        log.info('Undoing index replacement, settings %s with %s',
                 document._doc_type.index, old_index_name)
        document._doc_type.index = old_index_name


@app.task(queue='web')
def delete_objects_in_es(app_label, model_name, document_class, objects_id):
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)
    doc_obj = document()
    queryset = doc_obj.get_queryset()
    queryset = queryset.filter(id__in=objects_id)
    log.info("Deleting model: %s, '%s' objects", model.__name__, queryset.count())
    try:
        # This is a common case that we should be handling a better way
        doc_obj.update(queryset.iterator(), action='delete')
    except Exception:
        log.warning('Unable to delete a subset of files. Continuing.', exc_info=True)


@app.task(queue='web')
def create_new_es_index(app_label, model_name, index_name, new_index_name):
    model = apps.get_model(app_label, model_name)
    indices = registry.get_indices(models=[model])
    old_index = _get_index(indices=indices, index_name=index_name)
    new_index = old_index.clone(name=new_index_name)
    new_index.create()


@app.task(queue='web')
def switch_es_index(app_label, model_name, index_name, new_index_name):
    model = apps.get_model(app_label, model_name)
    indices = registry.get_indices(models=[model])
    old_index = _get_index(indices=indices, index_name=index_name)
    new_index = old_index.clone(name=new_index_name)
    old_index_actual_name = None

    if old_index.exists():
        # Alias can not be used to delete an index.
        # https://www.elastic.co/guide/en/elasticsearch/reference/6.0/indices-delete-index.html
        # So get the index actual name to delete it
        old_index_info = old_index.get()
        # The info is a dictionary and the key is the actual name of the index
        old_index_actual_name = list(old_index_info.keys())[0]

    # Put alias into the new index name and delete the old index if its exist
    new_index.put_alias(name=index_name)
    if old_index_actual_name:
        old_index.connection.indices.delete(index=old_index_actual_name)


@app.task(queue='web')
def index_missing_objects(app_label, model_name, document_class, index_generation_time):
    """
    Task to insure that none of the object is missed from indexing.

    The object ids are sent to `index_objects_to_es` task for indexing.
    While the task is running, new objects can be created/deleted in database
    and they will not be in the tasks for indexing into ES.
    This task will index all the objects that got into DB after the `latest_indexed` timestamp
    to ensure that everything is in ES index.
    """
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)
    query_string = '{}__lte'.format(document.modified_model_field)
    queryset = document().get_queryset().exclude(**{query_string: index_generation_time})
    document().update(queryset.iterator())

    log.info("Indexed %s missing objects from model: %s'", queryset.count(), model.__name__)

    # TODO: Figure out how to remove the objects from ES index that has been deleted


@app.task(queue='web')
def delete_old_search_queries_from_db():
    """
    Delete old SearchQuery objects.

    This is run by celery beat every day.
    """
    last_3_months = timezone.now().date() - timezone.timedelta(days=90)
    search_queries_qs = SearchQuery.objects.filter(
        created__date__lte=last_3_months,
    )

    if search_queries_qs.exists():
        log.info('Deleting search queries for last 3 months. Total: %s', search_queries_qs.count())
        search_queries_qs.delete()


@app.task(queue='web')
def record_search_query(project_slug, version_slug, query, total_results):
    """Record search query in database."""
    if not project_slug or not version_slug or not query or not total_results:
        log.debug(
            'Not recording the search query. Passed arguments: '
            'project_slug: %s, version_slug: %s, query: %s, total_results: %s' % (
                project_slug, version_slug, query, total_results
            )
        )
        return

    project_qs = Project.objects.filter(slug=project_slug)

    if not project_qs.exists():
        return

    project = project_qs.first()
    version_qs = Version.objects.filter(project=project, slug=version_slug)

    if not version_qs.exists():
        return

    version = version_qs.first()
    SearchQuery.objects.create(
        project=project,
        version=version,
        query=query,
    )
