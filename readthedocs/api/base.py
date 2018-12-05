# -*- coding: utf-8 -*-
"""API resources."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
from builtins import object

import redis
from django.conf.urls import url
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from tastypie import fields
from tastypie.authorization import DjangoAuthorization, ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.http import HttpCreated
from tastypie.resources import ModelResource
from tastypie.utils import dict_strip_unicode_keys, trailing_slash

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import ImportedFile, Project

from .utils import PostAuthentication

log = logging.getLogger(__name__)


class ProjectResource(ModelResource):

    """API resource for Project model."""

    users = fields.ToManyField('readthedocs.api.base.UserResource', 'users')

    class Meta(object):
        include_absolute_url = True
        allowed_methods = ['get', 'post', 'put']
        queryset = Project.objects.api()
        authentication = PostAuthentication()
        authorization = ReadOnlyAuthorization()
        excludes = ['path', 'featured', 'programming_language']
        filtering = {
            'users': ALL_WITH_RELATIONS,
            'slug': ALL_WITH_RELATIONS,
        }

    def get_object_list(self, request):
        self._meta.queryset = Project.objects.api(user=request.user)
        return super(ProjectResource, self).get_object_list(request)

    def dehydrate(self, bundle):
        bundle.data['downloads'] = bundle.obj.get_downloads()
        return bundle

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(
            request,
            request.body,
            format=request.META.get('CONTENT_TYPE', 'application/json'),
        )

        # Force this in an ugly way, at least should do "reverse"
        deserialized['users'] = ['/api/v1/user/%s/' % request.user.id]
        bundle = self.build_bundle(
            data=dict_strip_unicode_keys(deserialized), request=request)
        self.is_valid(bundle)
        updated_bundle = self.obj_create(bundle, request=request)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/schema/$' % self._meta.resource_name,
                self.wrap_view('get_schema'), name='api_get_schema'),
            url(
                r'^(?P<resource_name>%s)/search%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_search'), name='api_get_search'),
            url((r'^(?P<resource_name>%s)/(?P<slug>[a-z-_]+)/$') %
                self._meta.resource_name, self.wrap_view('dispatch_detail'),
                name='api_dispatch_detail'),
        ]


class VersionResource(ModelResource):

    """API resource for Version model."""

    project = fields.ForeignKey(ProjectResource, 'project', full=True)

    class Meta(object):
        allowed_methods = ['get', 'put', 'post']
        always_return_data = True
        queryset = Version.objects.api()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'project': ALL_WITH_RELATIONS,
            'slug': ALL_WITH_RELATIONS,
            'active': ALL,
        }

    def get_object_list(self, request):
        self._meta.queryset = Version.objects.api(user=request.user)
        return super(VersionResource, self).get_object_list(request)

    def build_version(self, request, **kwargs):
        project = get_object_or_404(Project, slug=kwargs['project_slug'])
        version = kwargs.get('version_slug', LATEST)
        version_obj = project.versions.get(slug=version)
        trigger_build(project=project, version=version_obj)
        return self.create_response(request, {'building': True})

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/schema/$' % self._meta.resource_name,
                self.wrap_view('get_schema'), name='api_get_schema'),
            url(
                r'^(?P<resource_name>%s)/(?P<project__slug>[a-z-_]+[a-z0-9-_]+)/$'  # noqa
                % self._meta.resource_name,
                self.wrap_view('dispatch_list'),
                name='api_version_list'),
            url((
                r'^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+[a-z0-9-_]+)/(?P'
                r'<version_slug>[a-z0-9-_.]+)/build/$') %
                self._meta.resource_name, self.wrap_view('build_version'),
                name='api_version_build_slug'),
        ]


class FileResource(ModelResource):

    """API resource for ImportedFile model."""

    project = fields.ForeignKey(ProjectResource, 'project', full=True)

    class Meta(object):
        allowed_methods = ['get', 'post']
        queryset = ImportedFile.objects.all()
        excludes = ['md5', 'slug']
        include_absolute_url = True
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/schema/$' % self._meta.resource_name,
                self.wrap_view('get_schema'), name='api_get_schema'),
            url(
                r'^(?P<resource_name>%s)/anchor%s$' %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('get_anchor'), name='api_get_anchor'),
        ]

    def get_anchor(self, request, **__):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        query = request.GET.get('q', '')
        try:
            redis_client = cache.get_client(None)
            redis_data = redis_client.keys('*redirects:v4*%s*' % query)
        except (AttributeError, redis.exceptions.ConnectionError):
            redis_data = []
        # -2 because http:
        urls = [
            ''.join(data.split(':')[6:]) for data in redis_data
            if 'http://' in data
        ]
        object_list = {'objects': urls}

        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class UserResource(ModelResource):

    """Read-only API resource for User model."""

    class Meta(object):
        allowed_methods = ['get']
        queryset = User.objects.all()
        fields = ['username', 'id']
        filtering = {
            'username': 'exact',
        }

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/schema/$' % self._meta.resource_name,
                self.wrap_view('get_schema'), name='api_get_schema'),
            url(
                r'^(?P<resource_name>%s)/(?P<username>[a-z-_]+)/$' %
                self._meta.resource_name, self.wrap_view('dispatch_detail'),
                name='api_dispatch_detail'),
        ]
