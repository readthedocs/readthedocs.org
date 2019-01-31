import logging

from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields

from readthedocs.projects.models import Project, HTMLFile

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])


log = logging.getLogger(__name__)


@project_index.doc_type
class ProjectDocument(DocType):

    # Metadata
    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })
    language = fields.KeywordField()

    class Meta(object):
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
class PageDocument(DocType):

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')

    # Searchable content
    title = fields.TextField(attr='processed_json.title')
    headers = fields.TextField(attr='processed_json.headers')
    content = fields.TextField(attr='processed_json.content')

    class Meta(object):
        model = HTMLFile
        fields = ('commit',)
        ignore_signals = True

    @classmethod
    def faceted_search(cls, query, user, projects_list=None, versions_list=None):
        from readthedocs.search.faceted_search import PageSearch
        kwargs = {
            'user': user,
            'query': query,
        }

        filters = {}
        if projects_list:
            filters['project'] = projects_list
        if versions_list:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return PageSearch(**kwargs)

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index"""
        queryset = super(PageDocument, self).get_queryset()

        # Exclude some files to not index
        excluded_files = ['search.html', 'genindex.html', 'py-modindex.html',
                          'search/index.html', 'genindex/index.html', 'py-modindex/index.html']

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.filter(project__documentation_type__contains='sphinx')
        for ending in excluded_files:
            queryset = queryset.exclude(path__endswith=ending)
        return queryset
