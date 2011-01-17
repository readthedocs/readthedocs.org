from django.contrib.auth.models import User
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from builds.models import Build
from projects.models import Project


class UserResource(ModelResource):
    class Meta:
        authentication = BasicAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post', 'put']
        queryset = User.objects.all()
        fields = ['username', 'first_name',
                  'last_name', 'last_login',
                  'id']
        filtering = {
            "username": ('exact', 'startswith'),
        }


class ProjectResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        authentication = BasicAuthentication()
        authorization = DjangoAuthorization()
        allowed_methods = ['get', 'post', 'put']
        queryset = Project.objects.all()
        filtering = {
            "slug": ('exact', 'startswith'),
        }
        excludes = ['build_pdf', 'path', 'skip', 'featured']


class BuildResource(ModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')

    class Meta:
        allowed_methods = ['get']
        queryset = Build.objects.all()
        filtering = {
            "project": ALL,
        }
