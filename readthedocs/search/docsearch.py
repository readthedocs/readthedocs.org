import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, renderers, exceptions
from elasticsearch_dsl import Search, Q

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, ProjectRelationship
from readthedocs.search.indexes import PageIndex

log = logging.getLogger(__name__)


class DocSearch(APIView):

    """
    Search a specific documentation version

    * Does permission checking against private projects
    * Searches subprojects for the same version, currently.
    """

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (renderers.JSONRenderer,)

    def _get_version(self, request):
        project_slug = request.GET.get('project', None)
        version_slug = request.GET.get('version', None)
        query = request.GET.get('q', None)

        if None in [project_slug, version_slug, query]:
            raise exceptions.ParseError('Need project, version, and q')
        try:
            project = Project.objects.get(slug=project_slug)
            version = Version.objects.public(
                user=request.user,
                project=project,
            ).get(slug=version_slug)
        except (Version.DoesNotExist, Project.DoesNotExist):
            raise exceptions.ParseError('Version not found')

        return (version, query)

    def _get_subversions(self, version, request):
        subprojects = version.project.subprojects.all()
        subversions = set()
        for rel in subprojects:
            project = rel.child
            versions = project.versions.public(request.user).filter(slug=version.slug)
            if versions:
                subversions.add(versions[0])
        return subversions

    def _add_canonical(self, version, results):
        # Supplement result paths with domain information on project
        hits = results.get('hits', {}).get('hits', [])
        for (n, hit) in enumerate(hits):
            if 'fields' not in hit:
                continue
            fields = hit['fields']
            search_project = fields['project'][0]
            path = fields['path'][0]
            canonical_url = version.project.get_docs_url(version_slug=version.slug)
            if search_project != version.project.slug:
                try:
                    subproject = version.project.subprojects.get(child__slug=search_project)
                    canonical_url = subproject.child.get_docs_url(
                        version_slug=version.slug
                    )
                except ProjectRelationship.DoesNotExist:
                    pass
            results['hits']['hits'][n]['fields']['link'] = (
                canonical_url + path
            )

    def get(self, request):
        """Perform search, supplement links by resolving project domains"""
        version, query = self._get_version(request)
        log.info("Doc search query performed: query=%s", query)
        subversions = self._get_subversions(version, request)
        results = execute_version_search(version=version, query=query, subversions=subversions)
        if results is None:
            return Response({'error': 'No results returned'},
                            status=status.HTTP_404_NOT_FOUND)
        self._add_canonical(version, results)
        # Strip unused internal state
        for key in ['_shards', 'took', 'timed_out']:
            if key in results:
                del results[key]
        return Response({'results': results})


def execute_version_search(version, query, subversions=None):

    all_projects = [version.project]
    if subversions:
        for subver in subversions:
            all_projects.append(subver.project)

    elastic_search = Search()

    elastic_search = elastic_search.filter(
        'terms', project=[proj.slug for proj in all_projects]
    ).filter(
        'term', version=version.slug
    )

    # Slop allows for less strict matching
    elastic_search = elastic_search.query(
        Q('multi_match', query=query, fields=['title^10', 'headers^5', 'content'], slop=2)
    ).fields(
        ["title", "project", "version", "path"]
    ).highlight('title').highlight('content')[:50]

    kwargs = {}
    if version.project.superprojects.exists():
        if version.project.superprojects.count() == 1:
            kwargs['routing'] = (version.project.superprojects.first()
                                 .parent.slug)
    else:
        kwargs['routing'] = version.project.slug

    page = PageIndex()
    response = page.search(body=elastic_search.to_dict(), **kwargs)
    return response
