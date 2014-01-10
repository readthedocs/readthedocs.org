import hashlib
import logging

from rest_framework import decorators, permissions, viewsets, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
import requests

from builds.models import Version
from djangome import views as djangome
from search.indexes import PageIndex, ProjectIndex, SectionIndex
from projects.models import Project

log = logging.getLogger(__name__)

@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def quick_search(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', 'latest')
    query = request.GET.get('q', None)
    redis_data = djangome.r.keys('redirects:v4:en:%s:%s:*%s*' % (version_slug, project_slug, query))
    ret_dict = {}
    for data in redis_data:
        if 'http://' in data or 'https://' in data:
            key = data.split(':')[5]
            value = ':'.join(data.split(':')[6:])
            ret_dict[key] = value
    return Response({"results": ret_dict})


@decorators.api_view(['POST'])
@decorators.permission_classes((permissions.IsAdminUser,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def index_search(request):
    page_obj = PageIndex()
    section_obj = SectionIndex()
    data = request.DATA['data']
    page_list = data['page_list']
    project_pk = data['project_pk']
    version_pk = data['version_pk']
    project = Project.objects.get(pk=project_pk)
    version = Version.objects.get(pk=version_pk)
    resp = requests.get('https://api.grokthedocs.com/api/v1/index/1/heatmap/', params={'project': project.slug, 'compare': True})
    ret_json = resp.json()
    project_scale = ret_json['scaled_project'][project.slug]

    project_obj = ProjectIndex()
    project_obj.index_document({
        'id': project.pk,
        'name': project.name,
        'slug': project.slug,
        'description': project.description,
        'lang': project.language,
        'author': [user.username for user in project.users.all()],
        'url': project.get_absolute_url(),
        '_boost': project_scale,
    })

    index_list = []
    section_index_list = []
    for page in page_list:
        log.debug("(API Index) %s:%s" % (project.slug, page['path']))
        page_scale = ret_json['scaled_page'].get(page['path'], 1)
        page_id = hashlib.md5('%s-%s-%s' % (project.slug, version.slug, page['path'])).hexdigest()
        index_list.append({
            'id': page_id,
            'project': project.slug,
            'version': version.slug,
            'path': page['path'],
            'title': page['title'],
            'headers': page['headers'],
            'content': page['content'],
            '_boost': page_scale + project_scale,
            })
        for section in page['sections']:
            section_index_list.append({
                'id': hashlib.md5('%s-%s-%s-%s' % (project.slug, version.slug, page['path'], section['id'])).hexdigest(),
                'project': project.slug,
                'version': version.slug,
                'path': page['path'],
                'page_id': section['id'],
                'title': section['title'],
                'content': section['content'],
                '_boost': page_scale,
            })
        section_obj.bulk_index(section_index_list, parent=page_id,
                               routing=project.slug)

    page_obj.bulk_index(index_list, parent=project.slug)
    return Response({'indexed': True})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def search(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', 'latest')
    query = request.GET.get('q', None)
    log.debug("(API Search) %s" % query)

    kwargs = {}
    body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": {"query": query, "boost": 10}}},
                    {"match": {"headers": {"query": query, "boost": 5}}},
                    {"match": {"content": {"query": query}}},
                ]
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "headers": {},
                "content": {},
            }
        },
        "fields": ["title", "project", "version", "path"],
        "size": 50  # TODO: Support pagination.
    }

    if project_slug:
        body['filter'] = {
            "and": [
                {"term": {"project": project_slug}},
                {"term": {"version": version_slug}},
            ]
        }
        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

    results = PageIndex().search(body, **kwargs)

    return Response({'results': results})


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def project_search(request):
    query = request.GET.get('q', None)

    log.debug("(API Project Search) %s" % (query))
    body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"name": {"query": query, "boost": 10}}},
                    {"match": {"description": {"query": query}}},
                ]
            },
        },
        "fields": ["name", "slug", "description", "lang"]
    }
    results = ProjectIndex().search(body)

    return Response({'results': results})

@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def section_search(request):
    """
    Search for a Section of content on Read the Docs.
    A Section is a subheading on a specific page.

    Query Thoughts
    --------------

    If you want to search across all documents, just query with a ``q`` GET arg.
    If you want to filter by a specific project, include a ``project`` GET arg.

    Facets
    ------

    When you search, you will have a ``project`` facet, which includes the number of matching sections per project.
    When you search inside a project, the ``path`` facet will show the number of matching sections per page.

    Possible GET args
    -----------------

    * q - The query string **Required**
    * project - A project slug *Optional*
    * version - A version slug *Optional*
    * path - A file path slug  *Optional*

    Example
    -------

        GET /api/v2/search/section/?q=virtualenv&project=django

    Current Query
    -------------

    """
    query = request.GET.get('q', None)
    if not query:
        return Response({'error': 'Search term required. Use the "q" GET arg to search. '}, status=status.HTTP_400_BAD_REQUEST)

    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', 'latest')
    path_slug = request.GET.get('path', None)

    log.debug("(API Section Search) [%s:%s] %s" % (project_slug, version_slug, query))

    kwargs = {}
    body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": {"query": query, "boost": 10}}},
                    {"match": {"content": {"query": query}}},
                ]
            }
        },
        "facets": {
            "project": {
                "terms": {"field": "project"},
                "facet_filter": {
                    "term": {"version": version_slug},
                } 
            },
        },
        "highlight": {
            "fields": {
                "title": {},
                "content": {},
            }
        },
        "fields": ["title", "project", "version", "path", "page_id", "content"],
        "size": 10  # TODO: Support pagination.
    }

    if project_slug:
        body['filter'] = {
            "and": [
                {"term": {"project": project_slug}},
                {"term": {"version": version_slug}},
            ]
        }
        body["facets"]['path'] = {
            "terms": {"field": "path"},
            "facet_filter": {
                "term": {"project": project_slug},
            } 
        },
        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

    if path_slug:
        body['filter'] = {
            "and": [
                {"term": {"path": path_slug}},
            ]
        }
        
    if path_slug and not project_slug:
        # Show facets when we only have a path
        body["facets"]['path'] = {
            "terms": {"field": "path"}
        }


    results = SectionIndex().search(body, **kwargs)

    return Response({'results': results})
