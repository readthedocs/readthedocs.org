import itertools
import sys
import textwrap
from datetime import datetime
from datetime import timedelta

import structlog
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django_elasticsearch_dsl.registries import registry

from readthedocs.builds.models import Version
from readthedocs.projects.models import HTMLFile
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.search import reindex_version
from readthedocs.search.documents import PageDocument
from readthedocs.search.documents import ProjectDocument
from readthedocs.search.tasks import create_new_es_index
from readthedocs.search.tasks import index_objects_to_es
from readthedocs.search.tasks import switch_es_index


log = structlog.get_logger(__name__)


class Command(BaseCommand):
    @staticmethod
    def _get_indexing_tasks(app_label, model_name, index_name, queryset, document_class):
        chunk_size = settings.ES_TASK_CHUNK_SIZE
        qs_iterator = queryset.values_list("pk", flat=True).iterator()

        data = {
            "app_label": app_label,
            "model_name": model_name,
            "document_class": document_class,
            "index_name": index_name,
        }
        current = 0
        while True:
            objects_id = list(itertools.islice(qs_iterator, chunk_size))
            if not objects_id:
                break
            current += len(objects_id)
            log.info("Total.", total=current)
            data["objects_id"] = objects_id
            yield index_objects_to_es.si(**data)

    def _run_reindex_tasks(self, models, queue):
        log.info("Adding indexing tasks to queue.", queue=queue)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        for model in models:
            if model == HTMLFile:
                self._reindex_files(queue=queue, timestamp=timestamp)
            elif model == Project:
                self._reindex_projects(queue=queue, timestamp=timestamp)
            else:
                log.warning("Re-index not available for model.", model_name=model.__name__)
                continue

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
                "Index name changed.",
                app_label=app_label,
                model_name=model_name,
                new_index_name=new_index_name,
                index_name=index_name,
            )

    def _reindex_from(self, days_ago, models, queue):
        functions = {
            HTMLFile: self._reindex_files_from,
            Project: self._reindex_projects_from,
        }
        for model in models:
            if model not in functions:
                log.warning("Re-index from not available for model.", model_name=model.__name__)
                continue
            functions[model](days_ago=days_ago, queue=queue)

    def _reindex_projects(self, queue, timestamp):
        document = ProjectDocument
        app_label = Project._meta.app_label
        model_name = Project.__name__
        index_name = document._index._name
        new_index_name = "{}_{}".format(index_name, timestamp)

        create_new_es_index(
            app_label=app_label,
            model_name=model_name,
            index_name=index_name,
            new_index_name=new_index_name,
        )
        log.info("Temporal index created.", index_name=new_index_name)

        queryset = document().get_queryset()
        indexing_tasks = self._get_indexing_tasks(
            app_label=app_label,
            model_name=model_name,
            queryset=queryset,
            index_name=new_index_name,
            document_class=str(document),
        )
        number_of_tasks = 0
        for task in indexing_tasks:
            task.apply_async(queue=queue)
            number_of_tasks += 1

        log.info(
            "Tasks issued successfully.",
            model_name=model_name,
            app_label=app_label,
            items=queryset.count(),
            number_of_tasks=number_of_tasks,
        )

    def _reindex_projects_from(self, days_ago, queue):
        """Reindex projects with recent changes."""
        since = datetime.now() - timedelta(days=days_ago)
        queryset = Project.objects.filter(modified_date__gte=since).distinct()
        app_label = Project._meta.app_label
        model_name = Project.__name__
        apply_async_kwargs = {"queue": queue}

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
                "Tasks issued successfully.",
                app_label=app_label,
                model_name=model_name,
                items=queryset.count(),
            )

    def _reindex_files(self, queue, timestamp):
        document = PageDocument
        app_label = HTMLFile._meta.app_label
        model_name = HTMLFile.__name__
        index_name = document._index._name
        new_index_name = "{}_{}".format(index_name, timestamp)
        create_new_es_index(
            app_label=app_label,
            model_name=model_name,
            index_name=index_name,
            new_index_name=new_index_name,
        )
        log.info("Temporal index created.", index_name=new_index_name)

        queryset = Version.objects.for_reindex().values_list("pk", flat=True)
        for version_id in queryset.iterator():
            reindex_version.apply_async(
                kwargs={
                    "version_id": version_id,
                    "search_index_name": new_index_name,
                },
                queue=queue,
            )

        log.info(
            "Tasks issued successfully for re-indexing of versions.",
            number_of_tasks=queryset.count(),
        )

    def _reindex_files_from(self, days_ago, queue):
        """Reindex HTML files from versions with recent builds."""
        since = datetime.now() - timedelta(days=days_ago)
        queryset = (
            Version.objects.for_reindex()
            .filter(builds__date__gte=since)
            .values_list("pk", flat=True)
        )
        for version_id in queryset.iterator():
            reindex_version.apply_async(
                kwargs={"version_id": version_id},
                queue=queue,
            )

        log.info(
            "Tasks issued successfully for re-indexing of versions.",
            number_of_tasks=queryset.count(),
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            dest="queue",
            action="store",
            required=True,
            help="Set the celery queue name for the task.",
        )
        parser.add_argument(
            "--change-index",
            dest="change_index",
            action="store",
            help=(
                "Change the index to the new one using the given timestamp and delete the old one. "
                "**This should be run after a re-index is completed**."
            ),
        )
        parser.add_argument(
            "--update-from",
            dest="update_from",
            type=int,
            action="store",
            help=("Re-index the models from the given days. This should be run after a re-index."),
        )
        parser.add_argument(
            "--models",
            dest="models",
            type=str,
            nargs="*",
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
        if options["models"]:
            models = [apps.get_model(model_name) for model_name in options["models"]]
        else:
            models = [Project, HTMLFile]

        queue = options["queue"]
        change_index = options["change_index"]
        update_from = options["update_from"]
        if change_index:
            timestamp = change_index
            print(
                f"You are about to change change the index from {models} to `[model]_{timestamp}`",
                "**The old index will be deleted!**",
            )
            if input("Continue? y/n: ") != "y":
                print("Task cancelled")
                sys.exit(1)
            self._change_index(models=models, timestamp=timestamp)
            print(
                textwrap.dedent(
                    """
                Indexes had been changed.

                Remember to re-index changed projects and versions with the
                `--update-from n` argument,
                where `n` is the number of days since the re-index.
                """
                )
            )
        elif update_from:
            print(
                "You are about to reindex all changed objects",
                f"from the latest {update_from} days from {models}",
            )
            if input("Continue? y/n: ") != "y":
                print("Task cancelled")
                sys.exit(1)
            self._reindex_from(days_ago=update_from, models=models, queue=queue)
        else:
            print(
                f"You are about to reindex all objects from {models}",
                f"into a new index in the {queue} queue.",
            )
            if input("Continue? y/n: ") != "y":
                print("Task cancelled")
                sys.exit(1)
            timestamp = self._run_reindex_tasks(models=models, queue=queue)
            print(
                textwrap.dedent(
                    f"""
                Re-indexing tasks have been created.
                Timestamp: {timestamp}

                Please monitor the tasks.
                After they are completed run the same command with the
                `--change-index {timestamp}` argument.
                """
                )
            )
