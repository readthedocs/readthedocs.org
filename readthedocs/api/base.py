import logging
import json

from django.contrib.auth.models import User
from django.conf.urls import url
from django.shortcuts import get_object_or_404

from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.resources import ModelResource
from tastypie.http import HttpCreated, HttpApplicationError
from tastypie.utils import dict_strip_unicode_keys, trailing_slash

from builds.models import Build, Version
from projects.models import Project, ImportedFile
from projects.utils import highest_version, mkversion, slugify_uniquely
from projects import tasks
from djangome import views as djangome

from .utils import SearchMixin, PostAuthentication, EnhancedModelResource

log = logging.getLogger(__name__)


class ProjectResource(ModelResource, SearchMixin):
    users = fields.ToManyField('api.base.UserResource', 'users')

    class Meta:
        include_absolute_url = True
        allowed_methods = ['get', 'post', 'put']
        queryset = Project.objects.public()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        excludes = ['path', 'featured']
        filtering = {
            "users": ALL_WITH_RELATIONS,
            "slug": ALL_WITH_RELATIONS,
        }

    def get_object_list(self, request):
        self._meta.queryset = Project.objects.public(user=request.user)
        return super(ProjectResource, self).get_object_list(request)

    def dehydrate(self, bundle):
        bundle.data['subdomain'] = "http://%s/" % bundle.obj.subdomain
        downloads = {}
        downloads['htmlzip'] = bundle.obj.get_htmlzip_url()
        downloads['epub'] = bundle.obj.get_epub_url()
        downloads['pdf'] = bundle.obj.get_pdf_url()
        downloads['manpage'] = bundle.obj.get_manpage_url()
        downloads['dash'] = bundle.obj.get_dash_url()
        bundle.data['downloads'] = downloads
        return bundle

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(
            request, request.raw_post_data,
            format=request.META.get('CONTENT_TYPE', 'application/json')
        )

        # Force this in an ugly way, at least should do "reverse"
        deserialized["users"] = ["/api/v1/user/%s/" % request.user.id]
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        updated_bundle = self.obj_create(bundle, request=request)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))



    def sync_versions(self, request, **kwargs):
        """
        Sync the version data in the repo (on the build server) with what we have in the database.

        Returns the identifiers for the versions that have been deleted.
        """
        project = get_object_or_404(Project, pk=kwargs['pk'])
        try:
            post_data = self.deserialize(
                request, request.raw_post_data,
                format=request.META.get('CONTENT_TYPE', 'application/json')
            )
            data = json.loads(post_data)
            self.method_check(request, allowed=['post'])
            self.is_authenticated(request)
            self.throttle_check(request)
            self.log_throttled_access(request)
            self._sync_versions(project, data['tags'])
            self._sync_versions(project, data['branches'])
            deleted_versions = self._delete_versions(project, data)
        except Exception, e:
            return self.create_response(
                request,
                {'exception': e.message},
                response_class=HttpApplicationError,
            )
        return self.create_response(request, deleted_versions)


    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name,
                self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/search%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\d+)/sync_versions%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view('sync_versions'), name="api_sync_versions"),
            url((r"^(?P<resource_name>%s)/(?P<slug>[a-z-_]+)/$")
                % self._meta.resource_name, self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]


class VersionResource(EnhancedModelResource):
    project = fields.ForeignKey(ProjectResource, 'project', full=True)

    class Meta:
        allowed_methods = ['get', 'put', 'post']
        always_return_data = True
        queryset = Version.objects.public()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            "project": ALL_WITH_RELATIONS,
            "slug": ALL_WITH_RELATIONS,
            "active": ALL,
        }

    # Find a better name for this before including it.
    # def dehydrate(self, bundle):
    #     bundle.data['subdomain'] = "http://%s/en/%s/" % (
    #         bundle.obj.project.subdomain, bundle.obj.slug
    #     )
    #     return bundle

    def get_object_list(self, request):
        self._meta.queryset = Version.objects.public(user=request.user,
                                                     only_active=False)
        return super(VersionResource, self).get_object_list(request)

    def version_compare(self, request, **kwargs):
        project = get_object_or_404(Project, slug=kwargs['project_slug'])
        highest = highest_version(project.versions.filter(active=True))
        base = kwargs.get('base', None)
        ret_val = {
            'project': highest[0],
            'version': highest[1],
            'is_highest': True,
        }
        if highest[0]:
            ret_val['url'] = highest[0].get_absolute_url()
            ret_val['slug'] = highest[0].slug,
        if base and base != 'latest':
            try:
                ver_obj = project.versions.get(slug=base)
                base_ver = mkversion(ver_obj)
                if base_ver:
                    # This is only place where is_highest can get set.  All
                    # error cases will be set to True, for non- standard
                    # versions.
                    ret_val['is_highest'] = base_ver >= highest[1]
                else:
                    ret_val['is_highest'] = True
            except (Version.DoesNotExist, TypeError):
                ret_val['is_highest'] = True
        return self.create_response(request, ret_val)

    def build_version(self, request, **kwargs):
        project = get_object_or_404(Project, slug=kwargs['project_slug'])
        version = kwargs.get('version_slug', 'latest')
        version_obj = project.versions.get(slug=version)
        tasks.update_docs.delay(pk=project.pk, version_pk=version_obj.pk)
        return self.create_response(request, {'building': True})

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$"
                % self._meta.resource_name,
                self.wrap_view('get_schema'),
                name="api_get_schema"),
            url((r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/highest/"
                 r"(?P<base>.+)/$")
                % self._meta.resource_name,
                self.wrap_view('version_compare'),
                name="version_compare"),
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/highest/$"
                % self._meta.resource_name,
                self.wrap_view('version_compare'),
                name="version_compare"),
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-_]+[a-z0-9-_]+)/$"  # noqa
                % self._meta.resource_name,
                self.wrap_view('dispatch_list'),
                name="api_version_list"),
            url((r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/(?P"
                 r"<version_slug>[a-z0-9-_.]+)/build/$")
                % self._meta.resource_name,
                self.wrap_view('build_version'),
                name="api_version_build_slug"),
        ]


class BuildResource(EnhancedModelResource):
    project = fields.ForeignKey('api.base.ProjectResource', 'project')
    version = fields.ForeignKey('api.base.VersionResource', 'version')

    class Meta:
        always_return_data = True
        include_absolute_url = True
        allowed_methods = ['get', 'post', 'put']
        queryset = Build.objects.all()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            "project": ALL_WITH_RELATIONS,
            "slug": ALL_WITH_RELATIONS,
            "type": ALL_WITH_RELATIONS,
            "state": ALL_WITH_RELATIONS,
        }

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$"
                % self._meta.resource_name,
                self.wrap_view('get_schema'),
                name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-_]+)/$" %
                self._meta.resource_name,
                self.wrap_view('dispatch_list'),
                name="build_list_detail"),
        ]


class FileResource(EnhancedModelResource, SearchMixin):
    project = fields.ForeignKey(ProjectResource, 'project', full=True)

    class Meta:
        allowed_methods = ['get', 'post']
        queryset = ImportedFile.objects.all()
        excludes = ['md5', 'slug']
        include_absolute_url = True
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        search_facets = ['project']

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$" %
                self._meta.resource_name,
                self.wrap_view('get_schema'),
                name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/search%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'),
                name="api_get_search"),
            url(r"^(?P<resource_name>%s)/anchor%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_anchor'),
                name="api_get_anchor"),
        ]

    def get_anchor(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        query = request.GET.get('q', '')
        redis_data = djangome.r.keys("*redirects:v4*%s*" % query)
        #-2 because http:
        urls = [''.join(data.split(':')[6:]) for data in redis_data
                if 'http://' in data]
        object_list = {'objects': urls}

        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class UserResource(ModelResource):
    class Meta:
        allowed_methods = ['get']
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name', 'last_login', 'id']
        filtering = {
            'username': 'exact',
        }

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$" %
                self._meta.resource_name,
                self.wrap_view('get_schema'),
                name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<username>[a-z-_]+)/$" %
                self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]
