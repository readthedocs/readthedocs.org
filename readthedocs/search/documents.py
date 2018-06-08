from django_elasticsearch_dsl import DocType, Index, fields

from readthedocs.projects.models import Project

project = Index('project')

project.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@project.doc_type
class ProjectDocument(DocType):

    class Meta:
        model = Project
        fields = ('name', 'slug', 'description', 'language')

    url = fields.TextField()
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })

    def prepare_url(self, instance):
        return instance.get_absolute_url()
