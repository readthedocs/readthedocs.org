from django.contrib.auth.models import User
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from tastypie.bundle import Bundle
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from builds.models import Build
from projects.models import Project


class EnhancedModelResource(ModelResource):
    def obj_get_list(self, request=None, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
        filters = None

        if hasattr(request, 'GET'):
            filters = request.GET

        applicable_filters = self.build_filters(filters=filters)
        applicable_filters.update(kwargs)

        try:
            return self.get_object_list(request).filter(**applicable_filters)
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")


class UserResource(ModelResource):
    class Meta:
        allowed_methods = ['get']
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name', 'last_login', 'id']

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<username>[a-z-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class ProjectResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        include_absolute_url = True
        allowed_methods = ['get']
        queryset = Project.objects.all()
        excludes = ['build_pdf', 'path', 'skip', 'featured']

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[a-z-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class BuildResource(EnhancedModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')

    class Meta:
        allowed_methods = ['get']
        queryset = Build.objects.all()

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_list_detail"),
        ]
