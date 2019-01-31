# -*- coding: utf-8 -*-

"""Search views."""
import collections
import logging
from pprint import pprint

from django.conf import settings
from django.shortcuts import render

from readthedocs.builds.constants import LATEST
from readthedocs.search.documents import PageDocument, ProjectDocument
from readthedocs.search.utils import get_project_list_or_404


log = logging.getLogger(__name__)
LOG_TEMPLATE = '(Elastic Search) [{user}:{type}] [{project}:{version}:{language}] {msg}'

UserInput = collections.namedtuple(
    'UserInput',
    (
        'query',
        'type',
        'project',
        'version',
        'taxonomy',
        'language',
    ),
)


def elastic_search(request):
    """Use Elasticsearch for global search."""
    user_input = UserInput(
        query=request.GET.get('q'),
        type=request.GET.get('type', 'project'),
        project=request.GET.get('project'),
        version=request.GET.get('version', LATEST),
        taxonomy=request.GET.get('taxonomy'),
        language=request.GET.get('language'),
    )
    results = ''

    facets = {}

    if user_input.query:
        if user_input.type == 'project':
            project_search = ProjectDocument.faceted_search(
                query=user_input.query, language=user_input.language
            )
            results = project_search.execute()
            facets = results.facets
        elif user_input.type == 'file':
            kwargs = {}
            if user_input.project:
                projects_list = get_project_list_or_404(
                    project_slug=user_input.project, user=request.user
                )
                project_slug_list = [project.slug for project in projects_list]
                kwargs['projects_list'] = project_slug_list
            if user_input.version:
                kwargs['versions_list'] = user_input.version

            page_search = PageDocument.faceted_search(
                query=user_input.query, **kwargs
            )
            results = page_search.execute()
            facets = results.facets

    if settings.DEBUG:
        print(pprint(results))
        print(pprint(facets))

    if user_input.query:
        user = ''
        if request.user.is_authenticated:
            user = request.user
        log.info(
            LOG_TEMPLATE.format(
                user=user,
                project=user_input.project or '',
                type=user_input.type or '',
                version=user_input.version or '',
                language=user_input.language or '',
                msg=user_input.query or '',
            ),
        )

    template_vars = user_input._asdict()
    template_vars.update({'results': results, 'facets': facets})
    return render(
        request,
        'search/elastic_search.html',
        template_vars,
    )
