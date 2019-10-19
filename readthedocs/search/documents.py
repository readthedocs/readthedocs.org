import logging

from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Index

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


@registry.register_document
@project_index.document
class ProjectDocument(RTDDocTypeMixin, Document):

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

    class Django:
        model = Project
        fields = ('name', 'slug', 'description')
        ignore_signals = True

    @classmethod
    def faceted_search(cls, query, user, language=None):
        from readthedocs.search.faceted_search import ProjectSearch
        kwargs = {
            'user': user,
            'query': query,
        }

        if language:
            kwargs['filters'] = {'language': language}

        return ProjectSearch(**kwargs)


@registry.register_document
@page_index.document
class PageDocument(RTDDocTypeMixin, Document):

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')
    full_path = fields.KeywordField(attr='path')

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

    class Django:
        model = HTMLFile
        fields = ('commit', 'build')
        ignore_signals = True

    def prepare_domains(self, html_file):
        """Prepares and returns the values for domains field."""
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

    @classmethod
    def faceted_search(
            cls, query, user, projects_list=None, versions_list=None,
            filter_by_user=True
    ):
        from readthedocs.search.faceted_search import PageSearch
        kwargs = {
            'user': user,
            'query': query,
            'filter_by_user': filter_by_user,
        }

        filters = {}
        if projects_list is not None:
            filters['project'] = projects_list
        if versions_list is not None:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return PageSearch(**kwargs)

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index."""
        queryset = super().get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.internal().filter(
            project__documentation_type__contains='sphinx'
        )

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
