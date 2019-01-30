from django.conf import settings
from django.db import models
from django_elasticsearch_dsl import DocType, Index, fields
from django.core.paginator import Paginator
from elasticsearch_dsl.query import SimpleQueryString, Bool

from readthedocs.projects.models import Project, HTMLFile
from readthedocs.search.faceted_search import ProjectSearch, FileSearch

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])


class RTDDocTypeMixin(object):

    """
    Override some methods of DocType of DED

    Changelog as following:
    - Do not index object that not exist in the provided queryset
    - Take additional argument in update method `index_name` to update specific index
    Issues:
    - https://github.com/sabricot/django-elasticsearch-dsl/issues/111
    """

    def _prepare_action(self, object_instance, action, index_name=None):
        """Overwrite to take `index_name` from parameters for setting index dynamically"""
        return {
            '_op_type': action,
            '_index': index_name or str(self._doc_type.index),
            '_type': self._doc_type.mapping.doc_type,
            '_id': object_instance.pk,
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }

    def _get_actions(self, object_list, action, index_name=None):
        """Overwrite to take `index_name` from parameters for setting index dynamically"""
        if self._doc_type.queryset_pagination is not None:
            paginator = Paginator(
                object_list, self._doc_type.queryset_pagination
            )
            for page in paginator.page_range:
                for object_instance in paginator.page(page).object_list:
                    yield self._prepare_action(object_instance, action, index_name)
        else:
            for object_instance in object_list:
                yield self._prepare_action(object_instance, action, index_name)

    def update(self, thing, refresh=None, action='index', index_name=None, **kwargs):
        """Update each document in ES for a model, iterable of models or queryset"""
        if refresh is True or (
            refresh is None and self._doc_type.auto_refresh
        ):
            kwargs['refresh'] = True

        # TODO: remove this overwrite when the issue has been fixed
        # https://github.com/sabricot/django-elasticsearch-dsl/issues/111
        if isinstance(thing, models.Model):
            # Its a model instance.

            # Do not need to check if its a delete action
            # Because while delete action, the object is already remove from database
            if action != 'delete':
                queryset = self.get_queryset()
                obj = queryset.filter(pk=thing.pk)
                if not obj.exists():
                    return None

            object_list = [thing]
        else:
            object_list = thing

        return self.bulk(
            self._get_actions(object_list, action, index_name=index_name), **kwargs
        )


@project_index.doc_type
class ProjectDocument(RTDDocTypeMixin, DocType):

    class Meta(object):
        model = Project
        fields = ('name', 'slug', 'description')
        ignore_signals = settings.ES_PROJECT_IGNORE_SIGNALS

    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })
    language = fields.KeywordField()

    # Fields to perform search with weight
    search_fields = ['name^5', 'description']

    @classmethod
    def faceted_search(cls, query, user, language=None, using=None, index=None):
        kwargs = {
            'user': user,
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': query,
            'fields': cls.search_fields
        }

        if language:
            kwargs['filters'] = {'language': language}

        return ProjectSearch(**kwargs)


@page_index.doc_type
class PageDocument(RTDDocTypeMixin, DocType):

    class Meta(object):
        model = HTMLFile
        fields = ('commit',)
        ignore_signals = settings.ES_PAGE_IGNORE_SIGNALS

    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')

    title = fields.TextField(attr='processed_json.title')
    headers = fields.TextField(attr='processed_json.headers')
    content = fields.TextField(attr='processed_json.content')
    path = fields.KeywordField(attr='processed_json.path')

    # Fields to perform search with weight
    search_fields = ['title^10', 'headers^5', 'content']
    # Exclude some files to not index
    excluded_files = ['search.html', 'genindex.html', 'py-modindex.html',
                      'search/index.html', 'genindex/index.html', 'py-modindex/index.html']

    @classmethod
    def faceted_search(
        cls, query, user, projects_list=None, versions_list=None, using=None, index=None
    ):
        es_query = cls.get_es_query(query=query)
        kwargs = {
            'user': user,
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': es_query,
            'fields': cls.search_fields
        }
        filters = {}

        if projects_list:
            filters['project'] = projects_list
        if versions_list:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return FileSearch(**kwargs)

    @classmethod
    def get_es_query(cls, query):
        """Return the Elasticsearch query generated from the query string"""
        all_queries = []

        # Need to search for both 'AND' and 'OR' operations
        # The score of AND should be higher as it satisfies both OR and AND
        for operator in ['AND', 'OR']:
            query_string = SimpleQueryString(query=query, fields=cls.search_fields,
                                             default_operator=operator)
            all_queries.append(query_string)

        # Run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        return bool_query

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index"""
        queryset = super(PageDocument, self).get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.filter(project__documentation_type__contains='sphinx')
        for ending in self.excluded_files:
            queryset = queryset.exclude(path__endswith=ending)
        return queryset
