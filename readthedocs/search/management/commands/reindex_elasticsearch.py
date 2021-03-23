import itertools
import logging
import textwrap
from datetime import datetime, timedelta

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django_elasticsearch_dsl.registries import registry

from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.tasks import (
    create_new_es_index,
    index_missing_objects,
    index_objects_to_es,
    switch_es_index,
)

log = logging.getLogger(__name__)


class Command(BaseCommand):

    @staticmethod
    def _get_indexing_tasks(app_label, model_name, index_name, queryset, document_class):
        chunk_size = settings.ES_TASK_CHUNK_SIZE
        qs_iterator = queryset.values_list('pk', flat=True).iterator()
        is_iterator_empty = False

        data = {
            'app_label': app_label,
            'model_name': model_name,
            'document_class': document_class,
            'index_name': index_name,
        }
        current = 0
        while True:
            objects_id = list(itertools.islice(qs_iterator, chunk_size))
            if not objects_id:
                break
            current += len(objects_id)
            log.info('Total: %s', current)
            data['objects_id'] = objects_id
            yield index_objects_to_es.si(**data)

    def _run_reindex_tasks(self, models, queue):
        apply_async_kwargs = {'queue': queue}
        log.info('Adding indexing tasks to queue %s', queue)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        for doc in registry.get_documents(models):
            queryset = doc().get_queryset()

            app_label = queryset.model._meta.app_label
            model_name = queryset.model.__name__

            index_name = doc._index._name
            new_index_name = "{}_{}".format(index_name, timestamp)

            # Set and create a temporal index for indexing.
            create_new_es_index(
                app_label=app_label,
                model_name=model_name,
                index_name=index_name,
                new_index_name=new_index_name,
            )
            doc._index._name = new_index_name
            log.info('Temporal index created: %s', new_index_name)

            indexing_tasks = self._get_indexing_tasks(
                app_label=app_label,
                model_name=model_name,
                queryset=queryset,
                index_name=new_index_name,
                document_class=str(doc),
            )
            for task in indexing_tasks:
                task.apply_async(**apply_async_kwargs)

            log.info(
                "Tasks issued successfully. model=%s.%s items=%s",
                app_label, model_name, str(queryset.count())
            )
        return timestamp

    def _change_index(self, models, timestamp):
        for doc in registry.get_documents(models):
            queryset = doc().get_queryset()
            app_label = queryset.model._meta.app_label
            model_name = queryset.model.__name__
            index_name = doc._index._name
            new_index_name = "{}_{}".format(index_name, timestamp)
            switch_es_index(
                app_label=app_label,
                model_name=model_name,
                index_name=index_name,
                new_index_name=new_index_name,
            )
            log.info(
                "Index name changed. model=%s.%s from=%s to=%s",
                app_label, model_name, new_index_name, index_name,
            )

    def _reindex_from(self, days_ago, models, queue):
        functions = {
            apps.get_model('projects.HTMLFile'): self._reindex_files_from,
            apps.get_model('projects.Project'): self._reindex_projects_from,
        }
        models = models or functions.keys()
        for model in models:
            if model not in functions:
                log.warning("Re-index from not available for model %s", model.__name__)
                continue
            functions[model](days_ago=days_ago, queue=queue)

    def _reindex_projects_from(self, days_ago, queue):
        """Reindex projects with recent changes."""
        since = datetime.now() - timedelta(days=days_ago)
        queryset = Project.objects.filter(modified_date__gte=since).distinct()
        app_label = Project._meta.app_label
        model_name = Project.__name__
        apply_async_kwargs = {'queue': queue}

        for doc in registry.get_documents(models=[Project]):
            indexing_tasks = self._get_indexing_tasks(
                app_label=app_label,
                model_name=model_name,
                queryset=queryset,
                index_name=doc._index._name,
                document_class=str(doc),
            )
            for task in indexing_tasks:
                task.apply_async(**apply_async_kwargs)
            log.info(
                "Tasks issued successfully. model=%s.%s items=%s",
                app_label, model_name, str(queryset.count())
            )

    def _reindex_files_from(self, days_ago, queue):
        """Reindex HTML files from versions with recent builds."""
        chunk_size = settings.ES_TASK_CHUNK_SIZE
        since = datetime.now() - timedelta(days=days_ago)
        queryset = Version.objects.filter(builds__date__gte=since).distinct()
        app_label = HTMLFile._meta.app_label
        model_name = HTMLFile.__name__
        apply_async_kwargs = {
            'queue': queue,
            'kwargs': {
                'app_label': app_label,
                'model_name': model_name,
            },
        }

        for doc in registry.get_documents(models=[HTMLFile]):
            apply_async_kwargs['kwargs']['document_class'] = str(doc)
            for version in queryset.iterator():
                project = version.project
                files_qs = (
                    HTMLFile.objects
                    .filter(version=version)
                    .values_list('pk', flat=True)
                    .iterator()
                )
                current = 0
                while True:
                    objects_id = list(itertools.islice(files_qs, chunk_size))
                    if not objects_id:
                        break
                    current += len(objects_id)
                    log.info(
                        'Re-indexing files. version=%s:%s total=%s',
                        project.slug, version.slug, current,
                    )
                    apply_async_kwargs['kwargs']['objects_id'] = objects_id
                    index_objects_to_es.apply_async(**apply_async_kwargs)

                log.info(
                    "Tasks issued successfully. version=%s:%s items=%s",
                    project.slug, version.slug, str(current),
                )

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            dest='queue',
            action='store',
            required=True,
            help="Set the celery queue name for the task."
        )
        parser.add_argument(
            '--change-index',
            dest='change_index',
            action='store',
            help=(
                "Change the index to the new one using the given timestamp and delete the old one. "
                "**This should be run after a re-index is completed**."
            ),
        )
        parser.add_argument(
            '--update-from',
            dest='update_from',
            type=int,
            action='store',
            help=(
                "Re-index the models from the given days. "
                "This should be run after a re-index."
            ),
        )
        parser.add_argument(
            '--models',
            dest='models',
            type=str,
            nargs='*',
            help=(
                "Specify the model to be updated in elasticsearch. "
                "The format is <app_label>.<model_name>"
            ),
        )

    def handle(self, *args, **options):
        """
        Index models into Elasticsearch index asynchronously using celery.

        You can specify model to get indexed by passing
        `--model <app_label>.<model_name>` parameter.
        Otherwise, it will re-index all the models
        """
        models = None
        if options['models']:
            models = [apps.get_model(model_name) for model_name in options['models']]

        queue = options['queue']
        change_index = options['change_index']
        update_from = options['update_from']
        if change_index:
            timestamp = change_index
            self._change_index(models=models, timestamp=timestamp)
            print(textwrap.dedent(
                """
                Indexes had been changed.

                Remember to re-index changed projects and versions with the
                `--update-from n` argument,
                where `n` is the number of days since the re-index.
                """
            ))
        elif update_from:
            self._reindex_from(days_ago=update_from, models=models, queue=queue)
        else:
            timestamp = self._run_reindex_tasks(models=models, queue=queue)
            print(textwrap.dedent(
                f"""
                Re-indexing tasks have been created.
                Timestamp: {timestamp}

                Please monitor the tasks.
                After they are completed run the same command with the
                `--change-index {timestamp}` argument.
                """
            ))
