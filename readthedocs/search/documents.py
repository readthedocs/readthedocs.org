from django.db import models
from django_elasticsearch_dsl import DocType, Index, fields

from readthedocs.projects.models import Project, HTMLFile
from .conf import SEARCH_EXCLUDED_FILE

from readthedocs.search.faceted_search import ProjectSearch

project_index = Index('project')

project_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


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


page_index = Index('page')

page_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


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

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index"""
        queryset = super(PageDocument, self).get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = (queryset.filter(project__documentation_type='sphinx')
                            .exclude(name__in=SEARCH_EXCLUDED_FILE))
        return queryset

    def update(self, thing, **kwargs):
        """Overwrite in order to index only certain files"""

        # Object not exist in the provided queryset should not be indexed
        # TODO: remove this overwrite when the issue has been fixed
        # See below link for more information
        # https://github.com/sabricot/django-elasticsearch-dsl/issues/111
        if isinstance(thing, HTMLFile):
            # Its a model instance.
            queryset = self.get_queryset()
            obj = queryset.filter(pk=thing.pk)
            if not obj.exists():
                return None

        return super(PageDocument, self).update(thing=thing, **kwargs)
