from django.contrib.auth.models import User
from django.conf.urls.defaults import url
from django.shortcuts import get_object_or_404
from django.http import HttpResponse



from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import NotFound
from tastypie.http import HttpCreated
from tastypie.utils import dict_strip_unicode_keys

from builds.models import Build, Version
from projects.models import Project
from projects.utils import highest_version

class PostAuthentication(BasicAuthentication):
    def is_authenticated(self, request, **kwargs):
        if request.method == "GET":
            return True
        return super(PostAuthentication, self).is_authenticated(request, **kwargs)


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
        allowed_methods = ['get', 'post']
        queryset = Project.objects.all()
        authentication = PostAuthentication()
        authorization = Authorization()
        excludes = ['use_virtualenv', 'path', 'skip', 'featured']

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))

        # Force this in an ugly way, at least should do "reverse"
        deserialized["user"] = "/api/v1/user/%s/" % request.user.id
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        updated_bundle = self.obj_create(bundle, request=request)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))


    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[a-z-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class BuildResource(EnhancedModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')

    class Meta:
        allowed_methods = ['get', 'post']
        queryset = Build.objects.all()

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_list_detail"),
        ]

class VersionResource(EnhancedModelResource):

    class Meta:
        queryset = Version.objects.all()

    def version_compare(self, request, **kwargs):
        project = get_object_or_404(Project, slug=kwargs['project_slug'])
        filter = kwargs.get('filter', None)
        if filter:
            highest = highest_version(project.versions.filter(slug__contains=filter))
        else:
            highest = highest_version(project.versions.all())
        ret_val = {
            'project': highest[0],
            'version': highest[1],
            'slug': highest[0].slug,
        }
        return self.create_response(request, ret_val)

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-]+)/highest/(?P<filter>.+)/$" % self._meta.resource_name, self.wrap_view('version_compare'), name="version_compare"),
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-]+)/highest/$" % self._meta.resource_name, self.wrap_view('version_compare'), name="version_compare"),
        ]
