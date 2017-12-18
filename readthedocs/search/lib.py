"""Utilities related to searching Elastic."""
from __future__ import absolute_import
from __future__ import print_function
from pprint import pprint

from django.conf import settings

from .indexes import PageIndex, ProjectIndex, SectionIndex

from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project
from readthedocs.search.signals import (before_project_search,
                                        before_file_search,
                                        before_section_search)


def search_project(request, query, language=None):
    """Search index for projects matching query."""
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
        "highlight": {
            "fields": {
                "name": {},
                "description": {},
            }
        },
        "fields": ["name", "slug", "description", "lang", "url"],
        "size": 50  # TODO: Support pagination.
    }

    if language:
        body['facets']['language']['facet_filter'] = {"term": {"lang": language}}
        body['filter'] = {"term": {"lang": language}}

    before_project_search.send(request=request, sender=ProjectIndex, body=body)

    return ProjectIndex().search(body)


def search_file(request, query, project_slug=None, version_slug=LATEST, taxonomy=None):
    """
    Search index for files matching query.

    Raises a 404 error on missing project

    :param request: request instance
    :param query: string to query for
    :param project_slug: :py:class:`Project` slug
    :param version_slug: slug for :py:class:`Project` version slug
    :param taxonomy: taxonomy for search
    """
    kwargs = {}
    body = {
        "query": {
            "bool": {
                "should": [
                    {"match_phrase": {
                        "title": {
                            "query": query,
                            "boost": 10,
                            "slop": 2,
                        },
                    }},
                    {"match_phrase": {
                        "headers": {
                            "query": query,
                            "boost": 5,
                            "slop": 3,
                        },
                    }},
                    {"match_phrase": {
                        "content": {
                            "query": query,
                            "slop": 5,
                        },
                    }},
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

    if project_slug or version_slug or taxonomy:
        final_filter = {"and": []}

        if project_slug:
            try:
                project = (Project.objects
                           .api(request.user)
                           .get(slug=project_slug))
                project_slugs = [project.slug]
                # We need to use the obtuse syntax here because the manager
                # doesn't pass along to ProjectRelationships
                project_slugs.extend(s.slug for s
                                     in Project.objects.public(
                                         request.user).filter(
                                         superprojects__parent__slug=project.slug))
                final_filter['and'].append({"terms": {"project": project_slugs}})

                # Add routing to optimize search by hitting the right shard.
                # This purposely doesn't apply routing if the project has more
                # than one parent project.
                if project.superprojects.exists():
                    if project.superprojects.count() == 1:
                        kwargs['routing'] = (project.superprojects.first()
                                             .parent.slug)
                else:
                    kwargs['routing'] = project_slug
            except Project.DoesNotExist:
                return None

        if version_slug:
            final_filter['and'].append({'term': {'version': version_slug}})

        if taxonomy:
            final_filter['and'].append({'term': {'taxonomy': taxonomy}})

        body['filter'] = final_filter
        body['facets']['project']['facet_filter'] = final_filter
        body['facets']['version']['facet_filter'] = final_filter
        body['facets']['taxonomy']['facet_filter'] = final_filter

    if settings.DEBUG:
        print("Before Signal")
        pprint(body)
    before_file_search.send(request=request, sender=PageIndex, body=body)
    if settings.DEBUG:
        print("After Signal")
        pprint(body)

    return PageIndex().search(body, **kwargs)


def search_section(request, query, project_slug=None, version_slug=LATEST,
                   path=None):
    """
    Search for a section of content.

    When you search, you will have a ``project`` facet, which includes the
    number of matching sections per project. When you search inside a project,
    the ``path`` facet will show the number of matching sections per page.

    :param request: Request instance
    :param query: string to use in query
    :param project_slug: :py:class:`Project` instance
    :param version_slug: :py:class:`Project` version instance
    :param taxonomy: search taxonomy
    """
    kwargs = {}
    body = {
        "query": {
            "bool": {
                "should": [
                    {"match_phrase": {
                        "title": {
                            "query": query,
                            "boost": 10,
                            "slop": 2,
                        },
                    }},
                    {"match_phrase": {
                        "content": {
                            "query": query,
                            "slop": 5,
                        },
                    }},
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
        body['facets']['path'] = {
            "terms": {"field": "path"},
            "facet_filter": {
                "term": {"project": project_slug},
            }
        },
        # Add routing to optimize search by hitting the right shard.
        kwargs['routing'] = project_slug

    if path:
        body['filter'] = {
            "and": [
                {"term": {"path": path}},
            ]
        }

    if path and not project_slug:
        # Show facets when we only have a path
        body['facets']['path'] = {
            "terms": {"field": "path"}
        }

    before_section_search.send(request=request, sender=PageIndex, body=body)

    return SectionIndex().search(body, **kwargs)
