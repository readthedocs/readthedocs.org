# -*- coding: utf-8 -*-

"""Search views."""
import collections
import logging
from pprint import pformat

from django.shortcuts import get_object_or_404, render

from readthedocs.builds.constants import LATEST
from readthedocs.search.documents import PageDocument, ProjectDocument
from readthedocs.search.utils import get_project_list_or_404
from readthedocs.projects.models import Project


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
    user = ''
    facets = {}

    if request.user.is_authenticated:
        user = request.user

    if user_input.query:
        if user_input.type == 'project':
            project_search = ProjectDocument.faceted_search(
                query=user_input.query, user=user, language=user_input.language
            )
            results = project_search.execute()
            facets = results.facets
        elif user_input.type == 'file':
            kwargs = {}
            if user_input.project:
                projects_list = get_project_list_or_404(
                    project_slug=user_input.project, user=user
                )
                project_slug_list = [project.slug for project in projects_list]
                kwargs['projects_list'] = project_slug_list
            if user_input.version:
                kwargs['versions_list'] = user_input.version

            page_search = PageDocument.faceted_search(
                query=user_input.query, user=user, **kwargs
            )
            results = page_search.execute()
            facets = results.facets

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

    if results:
        if user_input.type == 'file':
            # Change results to turn newlines in highlight into periods
            # https://github.com/rtfd/readthedocs.org/issues/5168
            for result in results:
                if hasattr(result.meta.highlight, 'content'):
                    for num, block in enumerate(result.meta.highlight.content):
                        new_text = block.replace('\n', '. ')
                        result.meta.highlight.content[num] = new_text

        log.debug('Search results: %s', pformat(results.to_dict()))
        log.debug('Search facets: %s', pformat(results.facets.to_dict()))

    template_vars = user_input._asdict()
    template_vars.update({'results': results, 'facets': facets})
    return render(
        request,
        'search/elastic_search.html',
        template_vars,
    )


def elastic_project_search(request, project_slug):
    """Use elastic search to search in a project."""
    queryset = Project.objects.protected(request.user)
    project = get_object_or_404(queryset, slug=project_slug)
    version_slug = request.GET.get('version', LATEST)
    query = request.GET.get('q', None)
    results = None

    if query:
        kwargs = {}
        kwargs['projects_list'] = [project.slug]
        kwargs['versions_list'] = version_slug
        user = ''
        if request.user.is_authenticated:
            user = request.user

        page_search = PageDocument.faceted_search(
            query=query, user=user, **kwargs
        )
        results = page_search.execute()

        log.debug('Search results: %s', pformat(results.to_dict()))
        log.debug('Search facets: %s', pformat(results.facets.to_dict()))

        log.info(
            LOG_TEMPLATE.format(
                user=user,
                project=project or '',
                type='inproject',
                version=version_slug or '',
                language='',
                msg=query or '',
            ),
        )

    return render(
        request,
        'search/elastic_project_search.html',
        {
            'project': project,
            'query': query,
            'results': results,
        },
    )
