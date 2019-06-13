import logging

from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields

from elasticsearch import Elasticsearch

from readthedocs.projects.models import HTMLFile, Project
from readthedocs.sphinx_domains.models import SphinxDomain


project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])

domain_conf = settings.ES_INDEXES['domain']
domain_index = Index(domain_conf['name'])
domain_index.settings(**domain_conf['settings'])

log = logging.getLogger(__name__)


class RTDDocTypeMixin:

    def update(self, *args, **kwargs):
        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic indexing to fix connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
        super().update(*args, **kwargs)


@domain_index.doc_type
class SphinxDomainDocument(RTDDocTypeMixin, DocType):
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    role_name = fields.KeywordField(attr='role_name')

    # For linking to the URL
    doc_name = fields.KeywordField(attr='doc_name')
    anchor = fields.KeywordField(attr='anchor')

    # For showing in the search result
    type_display = fields.TextField(attr='type_display')
    doc_display = fields.TextField(attr='doc_display')

    # Simple analyzer breaks on `.`,
    # otherwise search results are too strict for this use case
    name = fields.TextField(attr='name', analyzer='simple')
    display_name = fields.TextField(attr='display_name', analyzer='simple')

    modified_model_field = 'modified'

    class Meta:
        model = SphinxDomain
        fields = ('commit', 'build')
        ignore_signals = True

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index."""
        queryset = super().get_queryset()

        excluded_types = [
            {'domain': 'std', 'type': 'doc'},
            {'domain': 'std', 'type': 'label'},
        ]

        for exclude in excluded_types:
            queryset = queryset.exclude(**exclude)
        return queryset


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


@page_index.doc_type
class PageDocument(RTDDocTypeMixin, DocType):

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')

    # Searchable content
    title = fields.TextField(attr='processed_json.title')
    headers = fields.TextField(attr='processed_json.headers')
    content = fields.TextField(attr='processed_json.content')

    modified_model_field = 'modified_date'

    class Meta:
        model = HTMLFile
        fields = ('commit', 'build')
        ignore_signals = True

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
        queryset = super(PageDocument, self).get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.filter(
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
