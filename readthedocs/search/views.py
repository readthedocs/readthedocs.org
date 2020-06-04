"""Search views."""
import collections
import itertools
import logging
from operator import attrgetter

from django.shortcuts import get_object_or_404, render

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project
from readthedocs.search import utils
from readthedocs.search.faceted_search import (
    ALL_FACETS,
    PageSearch,
    ProjectSearch,
)

from .serializers import PageSearchSerializer, ProjectSearchSerializer

log = logging.getLogger(__name__)
LOG_TEMPLATE = '(Elastic Search) [%(user)s:%(type)s] [%(project)s:%(version)s:%(language)s] %(msg)s'

UserInput = collections.namedtuple(
    'UserInput',
    (
        'query',
        'type',
        'project',
        'version',
        'language',
        'role_name',
        'index',
    ),
)


def elastic_search(request, project_slug=None):
    """
    Global user search on the dashboard.

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

    serializers = collections.defaultdict(
        lambda: ProjectSearchSerializer,
        {
            'project': ProjectSearchSerializer,
            'file': PageSearchSerializer,
        }
    )

    results = []
    facets = {}

    if user_input.query:
        filters = {}

        for avail_facet in ALL_FACETS:
            value = getattr(user_input, avail_facet, None)
            if value:
                filters[avail_facet] = value

        search = search_facets[user_input.type](
            query=user_input.query,
            filters=filters,
            user=request.user,
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
    for facet in facets:
        value = getattr(user_input, facet, None)
        if value and value not in (val[0] for val in facets[facet]):
            facets[facet].insert(0, (value, 0, True))

    results = [
        serializers[user_input.type](result).data
        for result in results
    ]

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
