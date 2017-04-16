from pprint import pprint
import collections
import logging

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from readthedocs.builds.constants import LATEST
from readthedocs.search import lib as search_lib


log = logging.getLogger(__name__)
LOG_TEMPLATE = u"(Elastic Search) [{user}:{type}] [{project}:{version}:{language}] {msg}"


def elastic_search(request):
    """
    Use elastic search for global search
    """

    query = request.GET.get('q')
    type = request.GET.get('type', 'project')
    # File Facets
    project = request.GET.get('project')
    version = request.GET.get('version', LATEST)
    taxonomy = request.GET.get('taxonomy')
    language = request.GET.get('language')
    results = ""

    facets = {}

    if query:
        if type == 'project':
            results = search_lib.search_project(request, query, language=language)
        elif type == 'file':
            results = search_lib.search_file(request, query, project_slug=project,
                                             version_slug=version,
                                             taxonomy=taxonomy)

    if results:
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
        print pprint(results)
        print pprint(facets)

    if query:
        user = ''
        if request.user.is_authenticated():
            user = request.user
        log.info(LOG_TEMPLATE.format(
            user=user,
            project=project or '',
            type=type or '',
            version=version or '',
            language=language or '',
            msg=query or '',
        ))

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
