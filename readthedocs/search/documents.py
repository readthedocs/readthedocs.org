from django_elasticsearch_dsl import DocType, Index, fields

from readthedocs.projects.models import Project

from readthedocs.search.faceted_search import ProjectSearch

project_index = Index('project')

project_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@project_index.doc_type
class ProjectDocument(DocType):

    class Meta:
        model = Project
        fields = ('name', 'slug', 'description')

    url = fields.TextField()
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })
    language = fields.KeywordField()

    def prepare_url(self, instance):
        return instance.get_absolute_url()

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
