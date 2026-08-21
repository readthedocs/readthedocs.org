import structlog
from django.conf import settings
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl import Index
from django_elasticsearch_dsl import fields
from elasticsearch import Elasticsearch

from readthedocs.projects.models import HTMLFile
from readthedocs.projects.models import Project


project_conf = settings.ES_INDEXES["project"]
project_index = Index(project_conf["name"])
project_index.settings(**project_conf["settings"])

page_conf = settings.ES_INDEXES["page"]
page_index = Index(page_conf["name"])
page_index.settings(**page_conf["settings"])

log = structlog.get_logger(__name__)


class RTDDocTypeMixin:
    def update(self, *args, **kwargs):
        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.debug("Hacking Elastic indexing to fix connection pooling")
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL["default"])
        super().update(*args, **kwargs)


@project_index.document
class ProjectDocument(RTDDocTypeMixin, Document):
    """Document representation of a Project."""

    # Metadata
    url = fields.TextField(attr="get_absolute_url")
    users = fields.NestedField(
        properties={
            "username": fields.TextField(),
            "id": fields.IntegerField(),
        }
    )
    language = fields.KeywordField()

    name = fields.TextField(attr="name")
    slug = fields.TextField(attr="slug")
    description = fields.TextField(attr="description")

    modified_model_field = "modified_date"

    def get_queryset(self):
        """
        Additional filtering of default queryset.

        Don't include delisted projects.
        This will also break in-doc search for these projects,
        but it's not a priority to find a solution for this as long as "delisted" projects are
        understood to be projects with a negative reason for being delisted.
        """
        return (
            super()
            .get_queryset()
            .filter(search_indexing_enabled=True)
            .exclude(delisted=True)
            .exclude(is_spam=True)
        )

    class Django:
        model = Project
        fields = []
        ignore_signals = True


@page_index.document
class PageDocument(RTDDocTypeMixin, Document):
    """
    Document representation of a Page.

    Some text fields use the simple analyzer instead of the default (standard).
    Simple analyzer will break the text in non-letter characters,
    so a text like ``python.submodule`` will be broken like [python, submodule]
    instead of [python.submodule].
    See more at https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-analyzers.html  # noqa

    Some text fields use the ``with_positions_offsets`` term vector,
    this is to have faster highlighting on big documents.
    See more at https://www.elastic.co/guide/en/elasticsearch/reference/7.9/term-vector.html
    """

    # Metadata
    project = fields.KeywordField(attr="project.slug")
    version = fields.KeywordField(attr="version.slug")
    doctype = fields.KeywordField(attr="version.documentation_type")
    path = fields.KeywordField(attr="processed_json.path")
    full_path = fields.KeywordField(attr="path")
    rank = fields.IntegerField()

    # Searchable content
    title = fields.TextField(
        attr="processed_json.title",
    )
    sections = fields.NestedField(
        attr="processed_json.sections",
        properties={
            "id": fields.KeywordField(),
            "title": fields.TextField(),
            "content": fields.TextField(
                term_vector="with_positions_offsets",
            ),
        },
    )

    modified_model_field = "modified_date"

    class Django:
        model = HTMLFile
        fields = ("commit", "build")
        ignore_signals = True

    def prepare_rank(self, html_file):
        if not (-10 <= html_file.rank <= 10):
            return 0
        return html_file.rank

    def get_queryset(self):
        """Don't include ignored files and delisted projects."""
        queryset = super().get_queryset()
        queryset = (
            queryset.filter(project__search_indexing_enabled=True)
            .exclude(ignore=True)
            .exclude(project__delisted=True)
            .exclude(project__is_spam=True)
            .select_related("version", "project")
        )
        return queryset
