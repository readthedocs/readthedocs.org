
from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk_index

from django.conf import settings

from search.indexes import ProjectIndex, PageIndex

from elasticsearch_dsl import Search, Q


def search_project(query):
    s = Search(using=Elasticsearch(settings.ES_HOSTS)).index('readthedocs').doc_type('project')
    s.query("match", name=query, boost=10)
    s.query("match", description=query)
    s.fields(["name", "slug", "description", "lang"])

    body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"name": {"query": query, "boost": 10}}},
                    {"match": {"description": {"query": query}}},
                ]
            },
        },
        "facets": {
            "language": {
                "terms": {"field": "lang"},
            },
        },
        "fields": ["name", "slug", "description", "lang"]
    }
    results = ProjectIndex().search(body)
    #results = s.execute().to_dict()
    return results


def search_file(query, project=None, version='latest', taxonomy=None):

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
        "facets": {
            "taxonomy": {
                "terms": {"field": "taxonomy"},
            },
            "project": {
                "terms": {"field": "project"},
            },
            "version": {
                "terms": {"field": "version"},
            },
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

    if project or version or taxonomy:
        body['filter'] = {"and": []}

    if project:
        body['filter']['and'].append({'term': {'project': project}})

        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project

    if version:
        body['filter']['and'].append({'term': {'version': version}})

    if taxonomy:
        body['filter']['and'].append({'term': {'taxonomy': taxonomy}})

    results = PageIndex().search(body, **kwargs)
    return results
