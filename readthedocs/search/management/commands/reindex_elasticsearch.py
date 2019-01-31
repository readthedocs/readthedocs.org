import datetime
import logging

from celery import chord, chain
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from django_elasticsearch_dsl.registries import registry

from ...tasks import (index_objects_to_es, switch_es_index, create_new_es_index,
                      index_missing_objects)
from ...utils import get_chunk

log = logging.getLogger(__name__)


class Command(BaseCommand):

    @staticmethod
    def _get_indexing_tasks(app_label, model_name, queryset, document_class, index_name):
        total = queryset.count()
        chunks = get_chunk(total, settings.ES_TASK_CHUNK_SIZE)

        for chunk in chunks:
            data = {
                'app_label': app_label,
                'model_name': model_name,
                'document_class': document_class,
                'index_name': index_name,
                'chunk': chunk
            }
            yield index_objects_to_es.si(**data)

    def _run_reindex_tasks(self, models, queue):
        apply_async_kwargs = {'priority': 0}
        if queue:
            log.info('Adding indexing tasks to queue {0}'.format(queue))
            apply_async_kwargs['queue'] = queue
        else:
            log.info('Adding indexing tasks to default queue')

        index_time = timezone.now()
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        for doc in registry.get_documents(models):
            queryset = doc().get_queryset()
            # Get latest object from the queryset

            app_label = queryset.model._meta.app_label
            model_name = queryset.model.__name__

            index_name = doc._doc_type.index
            new_index_name = "{}_{}".format(index_name, timestamp)

            pre_index_task = create_new_es_index.si(app_label=app_label,
                                                    model_name=model_name,
                                                    index_name=index_name,
                                                    new_index_name=new_index_name)

            indexing_tasks = self._get_indexing_tasks(app_label=app_label, model_name=model_name,
                                                      queryset=queryset,
                                                      document_class=str(doc),
                                                      index_name=new_index_name)

            post_index_task = switch_es_index.si(app_label=app_label, model_name=model_name,
                                                 index_name=index_name,
                                                 new_index_name=new_index_name)

            # Task to run in order to add the objects
            # that has been inserted into database while indexing_tasks was running
            # We pass the creation time of latest object, so its possible to index later items
            missed_index_task = index_missing_objects.si(app_label=app_label,
                                                         model_name=model_name,
                                                         document_class=str(doc),
                                                         index_generation_time=index_time)

            # http://celery.readthedocs.io/en/latest/userguide/canvas.html#chords
            chord_tasks = chord(header=indexing_tasks, body=post_index_task)
            if queue:
                pre_index_task.set(queue=queue)
                chord_tasks.set(queue=queue)
                missed_index_task.set(queue=queue)
            # http://celery.readthedocs.io/en/latest/userguide/canvas.html#chain
            chain(pre_index_task, chord_tasks, missed_index_task).apply_async(**apply_async_kwargs)

            message = ("Successfully issued tasks for {}.{}, total {} items"
                       .format(app_label, model_name, queryset.count()))
            log.info(message)

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            dest='queue',
            action='store',
            help="Set the celery queue name for the task."
        )
        parser.add_argument(
            '--models',
            dest='models',
            type=str,
            nargs='*',
            help=("Specify the model to be updated in elasticsearch."
                  "The format is <app_label>.<model_name>")
        )

    def handle(self, *args, **options):
        """
        Index models into Elasticsearch index asynchronously using celery.

        You can specify model to get indexed by passing
        `--model <app_label>.<model_name>` parameter.
        Otherwise, it will reindex all the models
        """
        models = None
        if options['models']:
            models = [apps.get_model(model_name) for model_name in options['models']]

        queue = None
        if options.get('queue'):
            queue = options['queue']

        self._run_reindex_tasks(models=models, queue=queue)
