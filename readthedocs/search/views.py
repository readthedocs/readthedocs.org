from pprint import pprint
import collections
import os
import json
import logging
import mimetypes
import md5

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView
from django.utils.datastructures import SortedDict
from django.views.static import serve

from taggit.models import Tag
import requests

from builds.filters import VersionSlugFilter
from builds.models import Version
from projects.models import Project, ImportedFile
from search.indexes import PageIndex
from search import lib as search_lib


def elastic_search(request):
    """
    Use elastic search for global search
    """

    query = request.GET.get('q')
    type = request.GET.get('type', 'project')
    # File Facets
    project = request.GET.get('project')
    version = request.GET.get('version', 'latest')
    taxonomy = request.GET.get('taxonomy')
    language = request.GET.get('language')
    results = ""

    facets = {}

    if query:
        if type == 'project':
            results = search_lib.search_project(query)
        elif type == 'file':
            results = search_lib.search_file(query, project=project, version=version, taxonomy=taxonomy)

    if results:
        if settings.DEBUG:
            print pprint(results)
        # pre and post 1.0 compat
        for num, hit in enumerate(results['hits']['hits']):
            for key, val in hit['fields'].items():
                if isinstance(val, list):
                    results['hits']['hits'][num]['fields'][key] = val[0]

        if 'facets' in results:
            for facet_type in ['project', 'version', 'taxonomy', 'language']:
                if facet_type in results['facets']:
                    facets[facet_type] = collections.OrderedDict()
                    for term in results['facets'][facet_type]['terms']:
                        facets[facet_type][term['term']] = term['count']

    if settings.DEBUG:
        print pprint(facets)
    return render_to_response(
        'search/elastic_search.html',
        {
            # Input
            'query': query,
            'type': type,
            'project': project,
            'version': version,
            'taxonomy': taxonomy,
            'language': language,
            # Results
            'results': results,
            'facets': facets,
        },
        context_instance=RequestContext(request),
    )
