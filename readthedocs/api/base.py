import logging

from django.core.paginator import Paginator, InvalidPage
from django.contrib.auth.models import User
from django.conf.urls.defaults import url
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from haystack.utils import Highlighter
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie import http
from tastypie.utils.mime import build_content_type
from tastypie.http import HttpCreated
from tastypie.utils import dict_strip_unicode_keys, trailing_slash

from core.forms import FacetedSearchForm
from builds.models import Build, Version
from projects.models import Project, ImportedFile
from projects.utils import highest_version, mkversion
from projects import tasks
from djangome import views as djangome

log = logging.getLogger(__name__)

class SearchMixin(object):
    '''
    Adds a search api to any ModelResource provided the model is indexed.
    The search can be configured using the Meta class in each ModelResource.
    The search is limited to the model defined by the meta queryset. If the
    search is invalid, a 400 Bad Request will be raised.

    e.g.
        class Meta:
            # Return facet counts for each facetname
            search_facets = ['facetname1', 'facetname1']

            # Number of results returned per page 
            search_page_size = 20   

            # Highlight search terms in the text 
            search_highlight = True 
    '''
    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        object_list = self._search(request, 
            self._meta.queryset.model,
            facets = getattr(self._meta, 'search_facets', []),
            page_size = getattr(self._meta, 'search_page_size', 20),
            highlight = getattr(self._meta, 'search_highlight', True),
        )
        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def _url_template(self, query, selected_facets):
        '''
        Construct a url template to assist with navigating the resources.
        This looks a bit nasty but urllib.urlencode resulted in even 
        nastier output...
        '''
        query_params = []
        for facet in selected_facets:
            query_params.append(('selected_facets', facet))
        query_params += [('q', query), ('format', 'json'), ('page', '{0}')]
        query_string = '&'.join('='.join(p) for p in query_params)
        url_template = reverse('api_get_search', kwargs={
            'resource_name': self._meta.resource_name, 
            'api_name': 'v1'
        }) 
        return url_template + '?' + query_string

    def _search(self, request, model, facets=None, page_size=20, highlight=True):
        '''
        `facets`
            A list of facets to include with the results
        `models`
            Limit the search to one or more models
        '''
        form = FacetedSearchForm(request.GET, facets=facets or [], 
                                 models=(model,), load_all=True)
        if not form.is_valid():
            return self.error_response({'errors': form.errors }, request)
        results = form.search()

        paginator = Paginator(results, page_size)
        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404(ugettext("Sorry, no results on that page."))

        objects = []
        query = request.GET.get('q', '')
        highlighter = Highlighter(query)
        for result in page.object_list:
            if not result:
                continue
            text = result.text
            if highlight:
                text = highlighter.highlight(text)
            bundle = self.build_bundle(obj=result.object, request=request)
            bundle = self.full_dehydrate(bundle)
            bundle.data['text'] = text
            objects.append(bundle)

        url_template = self._url_template(query, form['selected_facets'].value())
        page_data = {
            'number': page.number,
            'per_page': paginator.per_page,
            'num_pages': paginator.num_pages,
            'page_range': paginator.page_range,
            'object_count': paginator.count,
            'url_template': url_template,
        }
        if page.has_next():
            page_data['url_next'] = url_template.format(page.next_page_number())
        if page.has_previous():
            page_data['url_prev'] = url_template.format(page.previous_page_number())

        object_list = {
            'page': page_data,
            'objects': objects,
        }
        if facets:
            object_list.update({'facets': results.facet_counts()})
        return object_list

 
    # XXX: This method is available in the latest tastypie, remove
    # once available in production.
    def error_response(self, errors, request):
        if request:
            desired_format = self.determine_format(request)
        else:
            desired_format = self._meta.default_format
        serialized = self.serialize(request, errors, desired_format)
        response = http.HttpBadRequest(content=serialized, content_type=build_content_type(desired_format))
        raise ImmediateHttpResponse(response=response)


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
            raise NotFound(ugettext("Invalid resource lookup data provided (mismatched type).: %(error)s") % {'error': e})


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
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<username>[a-z-_]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

class OwnerAuthorization(Authorization):
    def apply_limits(self, request, object_list):
        if request and hasattr(request, 'user') and request.method != 'GET':
            if request.user.is_authenticated():
                object_list = object_list.filter(users__in=[request.user])
            else:
                object_list = object_list.none()

        return object_list

class ProjectResource(ModelResource, SearchMixin):
    users = fields.ToManyField(UserResource, 'users')

    class Meta:
        include_absolute_url = True
        allowed_methods = ['get', 'post', 'put']
        queryset = Project.objects.all()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        excludes = ['path', 'featured']
        filtering = {
            "users": ALL_WITH_RELATIONS,
            "slug": ALL_WITH_RELATIONS,
        }

    def dehydrate(self, bundle):
        bundle.data['subdomain'] = "http://%s/" % bundle.obj.subdomain
        return bundle

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))

        # Force this in an ugly way, at least should do "reverse"
        deserialized["users"] = ["/api/v1/user/%s/" % request.user.id,]
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        updated_bundle = self.obj_create(bundle, request=request)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/(?P<slug>[a-z-_]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class BuildResource(EnhancedModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')
    version = fields.ForeignKey('api.base.VersionResource', 'version')

    class Meta:
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
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-_]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="build_list_detail"),
        ]

class VersionResource(EnhancedModelResource):
    project = fields.ForeignKey(ProjectResource, 'project', full=True)

    class Meta:
        queryset = Version.objects.all()
        allowed_methods = ['get', 'put', 'post']
        always_return_data = True
        queryset = Version.objects.all()
        authentication = PostAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            "project": ALL_WITH_RELATIONS,
            "slug": ALL_WITH_RELATIONS,
            "active": ALL,
        }

    #Find a better name for this before including it.
    #def dehydrate(self, bundle):
        #bundle.data['subdomain'] = "http://%s/en/%s/" % (bundle.obj.project.subdomain, bundle.obj.slug)
        #return bundle

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
            ret_val['slug'] =  highest[0].slug,
        if base and base != 'latest':
            try:
                ver_obj = project.versions.get(slug=base)
                base_ver = mkversion(ver_obj)
                if base_ver:
                    #This is only place where is_highest can get set.
                    #All error cases will be set to True, for non-
                    #standard versions.
                    ret_val['is_highest'] = base_ver >= highest[1]
                else:
                    ret_val['is_highest'] = True
            except (Version.DoesNotExist, TypeError) as e:
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
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/highest/(?P<base>.+)/$" % self._meta.resource_name, self.wrap_view('version_compare'), name="version_compare"),
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/highest/$" % self._meta.resource_name, self.wrap_view('version_compare'), name="version_compare"),
            url(r"^(?P<resource_name>%s)/(?P<project__slug>[a-z-_]+[a-z0-9-_]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="api_version_list"),
            url(r"^(?P<resource_name>%s)/(?P<project_slug>[a-z-_]+)/(?P<version_slug>[a-z0-9-_.]+)/build/$" % self._meta.resource_name, self.wrap_view('build_version'), name="api_version_build_slug"),
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
            url(r"^(?P<resource_name>%s)/schema/$" % self._meta.resource_name, self.wrap_view('get_schema'), name="api_get_schema"),
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/anchor%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_anchor'), name="api_get_anchor"),
        ]

    def get_anchor(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        query = request.GET.get('q', '')
        redis_data = djangome.r.keys("*redirects:v4*%s*" % query)
        #-2 because http:
        urls = [''.join(data.split(':')[6:]) for data in redis_data if 'http://' in data]

        """
        paginator = Paginator(urls, 20)

        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = [result for result in page.object_list]
        object_list = { 'objects': objects, }
        """
        object_list = { 'objects': urls }

        self.log_throttled_access(request)
        return self.create_response(request, object_list)
