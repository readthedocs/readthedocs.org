import logging

from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch import Elasticsearch
from elasticsearch_dsl.field import Keyword

from readthedocs.projects.models import HTMLFile, Project

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])

log = logging.getLogger(__name__)


# TODO: send this upstream (elasticsearch_dsl and django_elasticsearch_dsl).
class WildcardField(Keyword, fields.DEDField):

    name = 'wildcard'


class RTDDocTypeMixin:

    def update(self, *args, **kwargs):
        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic indexing to fix connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
        super().update(*args, **kwargs)


@project_index.document
class ProjectDocument(RTDDocTypeMixin, Document):

    """
    Document representation of a Project.

    We use multi-fields to be able to perform other kind of queries over the same field.
    ``raw`` fields are used for Wildcard queries.
    """

    # Metadata
    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(
        properties={
            'username': fields.TextField(),
            'id': fields.IntegerField(),
        }
    )
    language = fields.KeywordField()

    name = fields.TextField(
        attr='name',
        fields={
            'raw': WildcardField(),
        },
    )
    slug = fields.TextField(
        attr='slug',
        fields={
            'raw': WildcardField(),
        },
    )
    description = fields.TextField(
        attr='description',
        fields={
            'raw': WildcardField(),
        },
    )

    modified_model_field = 'modified_date'

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

    We use multi-fields to be able to perform other kind of queries over the same field.
    ``raw`` fields are used for Wildcard queries.

    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-analyzers.html
    """

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')
    full_path = fields.KeywordField(attr='path')
    rank = fields.IntegerField()

    # Searchable content
    title = fields.TextField(
        attr='processed_json.title',
        fields={
            'raw': WildcardField(),
        },
    )
    sections = fields.NestedField(
        attr='processed_json.sections',
        properties={
            'id': fields.KeywordField(),
            'title': fields.TextField(
                fields={
                    'raw': WildcardField(),
                },
            ),
            'content': fields.TextField(
                fields={
                    'raw': WildcardField(),
                },
            ),
        }
    )
    domains = fields.NestedField(
        properties={
            'role_name': fields.KeywordField(),

            # For linking to the URL
            'anchor': fields.KeywordField(),

            # For showing in the search result
            'type_display': fields.TextField(),
            'docstrings': fields.TextField(
                fields={
                    'raw': WildcardField(),
                },
            ),

            'name': fields.TextField(
                # Simple analyzer breaks on `.`,
                # otherwise search results are too strict for this use case
                analyzer='simple',
                fields={
                    'raw': WildcardField(),
                },
            ),
        }
    )

    modified_model_field = 'modified_date'

    class Django:
        model = HTMLFile
        fields = ('commit', 'build')
        ignore_signals = True

    def prepare_rank(self, html_file):
        if not (-10 <= html_file.rank <= 10):
            return 0
        return html_file.rank

    def prepare_domains(self, html_file):
        """Prepares and returns the values for domains field."""
        if not html_file.version.is_sphinx_type:
            return []

        all_domains = []
        try:
            domains_qs = html_file.sphinx_domains.exclude(
                domain='std',
                type__in=['doc', 'label']
            ).iterator()

            all_domains = [
                {
                    'role_name': domain.role_name,
                    'anchor': domain.anchor,
                    'type_display': domain.type_display,
                    'docstrings': html_file.processed_json.get(
                        'domain_data', {}
                    ).get(domain.anchor, ''),
                    'name': domain.name,
                }
                for domain in domains_qs
            ]

            log.debug(
                "[%s] [%s] Total domains for file %s are: %s",
                html_file.project.slug,
                html_file.version.slug,
                html_file.path,
                len(all_domains)
            )

        except Exception:
            log.exception(
                "[%s] [%s] Error preparing domain data for file %s",
                html_file.project.slug,
                html_file.version.slug,
                html_file.path
            )

        return all_domains

    def get_queryset(self):
        """
        Ignore certain files from indexing.

        - Files from external versions
        - Ignored files
        """
        queryset = super().get_queryset()
        queryset = (
            queryset
            .internal()
            .exclude(ignore=True)
        )
        return queryset
