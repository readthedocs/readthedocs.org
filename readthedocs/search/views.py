"""Search views."""
import collections
import logging
from pprint import pformat

from django.shortcuts import get_object_or_404, render

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project
from readthedocs.search.faceted_search import (
    ALL_FACETS,
    PageSearch,
    ProjectSearch,
)
from readthedocs.search import utils


log = logging.getLogger(__name__)
LOG_TEMPLATE = '(Elastic Search) [%(user)s:%(type)s] [%(project)s:%(version)s:%(language)s] %(msg)s'

UserInput = collections.namedtuple(
    'UserInput',
    (
        'query',
        'type',
        'project',
        'version',
        'taxonomy',
        'language',
        'role_name',
        'index',
    ),
)


def elastic_search(request, project_slug=None):
    """
    Global user search on the dashboard

    This is for both the main search and project search.

    :param project_slug: Sent when the view is a project search
    """

    request_type = None
    if project_slug:
        queryset = Project.objects.protected(request.user)
        project_obj = get_object_or_404(queryset, slug=project_slug)
        request_type = request.GET.get('type', 'file')

    user_input = UserInput(
        query=request.GET.get('q'),
        type=request_type or request.GET.get('type', 'project'),
        project=project_slug or request.GET.get('project'),
        version=request.GET.get('version', LATEST),
        taxonomy=request.GET.get('taxonomy'),
        language=request.GET.get('language'),
        role_name=request.GET.get('role_name'),
        index=request.GET.get('index'),
    )
    search_facets = collections.defaultdict(
        lambda: ProjectSearch,
        {
            'project': ProjectSearch,
            'file': PageSearch,
        }
    )

    results = None
    facets = {}

    if user_input.query:
        kwargs = {}

        for avail_facet in ALL_FACETS:
            value = getattr(user_input, avail_facet, None)
            if value:
                kwargs[avail_facet] = value

        search = search_facets[user_input.type](
            query=user_input.query, user=request.user, **kwargs
        )
        results = search[:50].execute()
        facets = results.facets

        log.info(
            LOG_TEMPLATE,
            {
                'user': request.user,
                'project': user_input.project or '',
                'type': user_input.type or '',
                'version': user_input.version or '',
                'language': user_input.language or '',
                'msg': user_input.query or '',
            }
        )

    # Make sure our selected facets are displayed even when they return 0 results
    for avail_facet in ALL_FACETS:
        value = getattr(user_input, avail_facet, None)
        if not value or avail_facet not in facets:
            continue
        if value not in [val[0] for val in facets[avail_facet]]:
            facets[avail_facet].insert(0, (value, 0, True))

    if results:

        # sorting inner_hits (if present)
        try:
            for hit in results.hits.hits:
                sections = hit['inner_hits'].get('sections', [])
                domains = hit['inner_hits'].get('domains', [])
                all_results = list(sections) + list(domains)

                sorted_results = [
                    {
                        'type': hit._nested.field,

                        # here _source term is not used because
                        # django gives error if the names of the
                        # variables start with underscore
                        'source': hit._source.to_dict(),

                        'highlight': utils._remove_newlines_from_dict(
                            hit.highlight.to_dict()
                        ),
                    }
                    for hit in sorted(all_results, key=utils._get_hit_score, reverse=True)
                ]

                hit['inner_hits'].pop('sections', None)
                hit['inner_hits'].pop('domains', None)
                hit['inner_hits'] = sorted_results

        except Exception as e:
            log.debug('Error occurred while sorting inner_hits', e)

        log.debug('Search results: %s', pformat(results.to_dict()))
        log.debug('Search facets: %s', pformat(results.facets.to_dict()))

    template_vars = user_input._asdict()
    template_vars.update({
        'results': results,
        'facets': facets,
    })

    if project_slug:
        template_vars.update({'project_obj': project_obj})

    return render(
        request,
        'search/elastic_search.html',
        template_vars,
    )
