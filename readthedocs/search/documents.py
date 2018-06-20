from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields

from readthedocs.projects.models import Project, HTMLFile
from .conf import SEARCH_EXCLUDED_FILE

from readthedocs.search.faceted_search import ProjectSearch, FileSearch

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])


@project_index.doc_type
class ProjectDocument(DocType):

    class Meta(object):
        model = Project
        fields = ('name', 'slug', 'description')

    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })
    language = fields.KeywordField()

    @classmethod
    def faceted_search(cls, query, language=None, using=None, index=None):
        kwargs = {
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': query
        }

        if language:
            kwargs['filters'] = {'language': language}

        return ProjectSearch(**kwargs)


@page_index.doc_type
class PageDocument(DocType):

    class Meta(object):
        model = HTMLFile
        fields = ('commit',)

    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')

    title = fields.TextField(attr='processed_json.title')
    headers = fields.TextField(attr='processed_json.headers')
    content = fields.TextField(attr='processed_json.content')
    path = fields.TextField(attr='processed_json.path')

    @classmethod
    def faceted_search(cls, query, projects_list=None, versions_list=None, using=None, index=None):
        kwargs = {
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': query
        }
        filters = {}

        if projects_list:
            filters['project'] = projects_list
        if versions_list:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return FileSearch(**kwargs)

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index"""
        queryset = super(PageDocument, self).get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = (queryset.filter(project__documentation_type='sphinx')
                            .exclude(name__in=SEARCH_EXCLUDED_FILE))
        return queryset

    def update(self, thing, refresh=None, action='index', **kwargs):
        """Overwrite in order to index only certain files"""
        # Object not exist in the provided queryset should not be indexed
        # TODO: remove this overwrite when the issue has been fixed
        # See below link for more information
        # https://github.com/sabricot/django-elasticsearch-dsl/issues/111
        # Moreover, do not need to check if its a delete action
        # Because while delete action, the object is already remove from database
        if isinstance(thing, HTMLFile) and action != 'delete':
            # Its a model instance.
            queryset = self.get_queryset()
            obj = queryset.filter(pk=thing.pk)
            if not obj.exists():
                return None

        return super(PageDocument, self).update(thing=thing, refresh=refresh,
                                                action=action, **kwargs)
