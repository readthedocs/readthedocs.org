# -*- coding: utf-8 -*-
"""Search views."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import collections
import logging
from pprint import pprint

from django.conf import settings
from django.shortcuts import render, get_object_or_404

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project
from readthedocs.search import lib as search_lib
from readthedocs.search.documents import ProjectDocument, PageDocument

log = logging.getLogger(__name__)
LOG_TEMPLATE = u'(Elastic Search) [{user}:{type}] [{project}:{version}:{language}] {msg}'

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
            project_search = ProjectDocument.faceted_search(query=user_input.query,
                                                            language=user_input.language)
            results = project_search.execute()
            facets = results.facets
        elif user_input.type == 'file':
            kwargs = {}
            if user_input.project:
                queryset = Project.objects.api(request.user).only('slug')
                project = get_object_or_404(queryset, slug=user_input.project)

                subprojects_slug = (queryset.filter(superprojects__parent_id=project.id)
                                            .values_list('slug', flat=True))

                projects_list = [project.slug] + list(subprojects_slug)
                kwargs['projects_list'] = projects_list
            if user_input.version:
                kwargs['versions_list'] = user_input.version

            page_search = PageDocument.faceted_search(query=user_input.query, **kwargs)
            results = page_search.execute()
            facets = results.facets

    if settings.DEBUG:
        print(pprint(results))
        print(pprint(facets))

    if user_input.query:
        user = ''
        if request.user.is_authenticated():
            user = request.user
        log.info(
            LOG_TEMPLATE.format(
                user=user,
                project=user_input.project or '',
                type=user_input.type or '',
                version=user_input.version or '',
                language=user_input.language or '',
                msg=user_input.query or '',
            ))

    template_vars = user_input._asdict()
    template_vars.update({
        'results': results,
        'facets': facets
    })
    return render(
        request,
        'search/elastic_search.html',
        template_vars,
    )
