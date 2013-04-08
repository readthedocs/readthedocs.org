import logging

from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from haystack.utils import Highlighter
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie import http
from tastypie.utils.mime import build_content_type

from core.forms import FacetedSearchForm

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
        object_list = self._search(
            request, self._meta.queryset.model,
            facets=getattr(self._meta, 'search_facets', []),
            page_size=getattr(self._meta, 'search_page_size', 20),
            highlight=getattr(self._meta, 'search_highlight', True))
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

    def _search(self, request, model, facets=None, page_size=20,
                highlight=True):
        '''
        `facets`
            A list of facets to include with the results
        `models`
            Limit the search to one or more models
        '''
        form = FacetedSearchForm(request.GET, facets=facets or [],
                                 models=(model,), load_all=True)
        if not form.is_valid():
            return self.error_response({'errors': form.errors}, request)
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

        url_template = self._url_template(query,
                                          form['selected_facets'].value())
        page_data = {
            'number': page.number,
            'per_page': paginator.per_page,
            'num_pages': paginator.num_pages,
            'page_range': paginator.page_range,
            'object_count': paginator.count,
            'url_template': url_template,
        }
        if page.has_next():
            page_data['url_next'] = url_template.format(
                page.next_page_number())
        if page.has_previous():
            page_data['url_prev'] = url_template.format(
                page.previous_page_number())

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
        response = http.HttpBadRequest(
            content=serialized,
            content_type=build_content_type(desired_format))
        raise ImmediateHttpResponse(response=response)


class PostAuthentication(BasicAuthentication):
    def is_authenticated(self, request, **kwargs):
        val = super(PostAuthentication, self).is_authenticated(request,
                                                               **kwargs)
        if request.method == "GET":
            return True
        return val


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
            raise NotFound(ugettext("Invalid resource lookup data provided "
                                    "(mismatched type).: %(error)s") % {
                                        'error': e
                                    })


class OwnerAuthorization(Authorization):
    def apply_limits(self, request, object_list):
        if request and hasattr(request, 'user') and request.method != 'GET':
            if request.user.is_authenticated():
                object_list = object_list.filter(users__in=[request.user])
            else:
                object_list = object_list.none()

        return object_list
