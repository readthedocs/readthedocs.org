# -*- coding: utf-8 -*-
"""Search views."""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import collections
import logging
from pprint import pprint

from django.conf import settings
from django.shortcuts import render

from readthedocs.builds.constants import LATEST
from readthedocs.search import lib as search_lib

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
            results = search_lib.search_project(
                request, user_input.query, language=user_input.language)
        elif user_input.type == 'file':
            results = search_lib.search_file(
                request, user_input.query, project_slug=user_input.project,
                version_slug=user_input.version, taxonomy=user_input.taxonomy)

    if results:
        # pre and post 1.0 compat
        for num, hit in enumerate(results['hits']['hits']):
            for key, val in list(hit['fields'].items()):
                if isinstance(val, list):
                    results['hits']['hits'][num]['fields'][key] = val[0]

        if 'facets' in results:
            for facet_type in ['project', 'version', 'taxonomy', 'language']:
                if facet_type in results['facets']:
                    facets[facet_type] = collections.OrderedDict()
                    for term in results['facets'][facet_type]['terms']:
                        facets[facet_type][term['term']] = term['count']

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
        'facets': facets,
    })
    return render(
        request,
        'search/elastic_search.html',
        template_vars,
    )
