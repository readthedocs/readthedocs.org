import logging

from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch import Elasticsearch

from readthedocs.projects.models import HTMLFile, Project

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])

log = logging.getLogger(__name__)


class RTDDocTypeMixin:

    def update(self, *args, **kwargs):
        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic indexing to fix connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
        super().update(*args, **kwargs)


@project_index.doc_type
class ProjectDocument(RTDDocTypeMixin, DocType):

    # Metadata
    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(
        properties={
            'username': fields.TextField(),
            'id': fields.IntegerField(),
        }
    )
    language = fields.KeywordField()

    modified_model_field = 'modified_date'

    class Meta:
        model = Project
        fields = ('name', 'slug', 'description')
        ignore_signals = True


@page_index.doc_type
class PageDocument(RTDDocTypeMixin, DocType):

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')
    full_path = fields.KeywordField(attr='path')
    rank = fields.FloatField()

    # Searchable content
    title = fields.TextField(attr='processed_json.title')
    sections = fields.NestedField(
        attr='processed_json.sections',
        properties={
            'id': fields.KeywordField(),
            'title': fields.TextField(),
            'content': fields.TextField(),
        }
    )
    domains = fields.NestedField(
        properties={
            'role_name': fields.KeywordField(),

            # For linking to the URL
            'anchor': fields.KeywordField(),

            # For showing in the search result
            'type_display': fields.TextField(),
            'docstrings': fields.TextField(),

            # Simple analyzer breaks on `.`,
            # otherwise search results are too strict for this use case
            'name': fields.TextField(analyzer='simple'),
        }
    )

    modified_model_field = 'modified_date'

    class Meta:
        model = HTMLFile
        fields = ('commit', 'build')
        ignore_signals = True

    def prepare_rank(self, html_file):
        """
        Maps the page rank to a value that is expected by ES.

        ES expects a rank to be a number greater than 0,
        but the user can set this between [-10, +10].
        We map that range to [0.01, 2] (21 possible values).
        """
        ranks = [
            0.01,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1,
            1.1,
            1.2,
            1.3,
            1.4,
            1.5,
            1.6,
            1.7,
            1.8,
            1.9,
            2,
        ]
        if html_file.rank is None or not (-10 <= html_file.rank <= 10):
            return 1
        return ranks[html_file.rank + 10]

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

            log.debug("[%s] [%s] Total domains for file %s are: %s" % (
                html_file.project.slug,
                html_file.version.slug,
                html_file.path,
                len(all_domains),
            ))

        except Exception:
            log.exception("[%s] [%s] Error preparing domain data for file %s" % (
                html_file.project.slug,
                html_file.version.slug,
                html_file.path,
            ))

        return all_domains

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index."""
        queryset = super().get_queryset()

        # Do not index files from external versions
        queryset = queryset.internal().all()

        # TODO: Make this smarter
        # This was causing issues excluding some valid user documentation pages
        # excluded_files = [
        #     'search.html',
        #     'genindex.html',
        #     'py-modindex.html',
        #     'search/index.html',
        #     'genindex/index.html',
        #     'py-modindex/index.html',
        # ]
        # for ending in excluded_files:
        #     queryset = queryset.exclude(path=ending)

        return queryset
