from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.conf import settings

from distlib.version import UnsupportedVersionError
from rest_framework import decorators, permissions, viewsets, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from betterversion.better import version_windows, BetterVersion 
from builds.models import Version
from projects.models import Project, EmailHook
from search.indexes import Page as PageIndex, Project as ProjectIndex
from djangome import views as djangome

from .serializers import ProjectSerializer
from .permissions import RelatedProjectIsOwner

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = Project

    @decorators.link()
    def valid_versions(self, request, **kwargs):
        """
        Maintain state of versions that are wanted.
        """
        project = get_object_or_404(Project, pk=kwargs['pk'])
        if not project.num_major or not project.num_minor or not project.num_point:
            return Response({'error': 'Project does not support point version control'}, status=status.HTTP_400_BAD_REQUEST)
        versions = []
        for ver in project.versions.all():
            try:
                versions.append(BetterVersion(ver.verbose_name))
            except UnsupportedVersionError:
                # Probably a branch
                pass
        active_versions = version_windows(
            versions, 
            major=project.num_major, 
            minor=project.num_minor, 
            point=project.num_point,
            flat=True,
        )
        version_strings = [v._string for v in active_versions]
        # Disable making old versions inactive for now.
        #project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(verbose_name__in=version_strings).update(active=True)
        return Response({
            'flat': version_strings,
            })

    @decorators.link()
    def translations(self, request, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        queryset = project.translations.all()
        return Response({
            'translations': ProjectSerializer(queryset, many=True).data
        })

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = EmailHook

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.filter(project__users__in=[user.pk])

class VersionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = Version

    @decorators.link()
    def downloads(self, request, **kwargs):
        version = get_object_or_404(Version, pk=kwargs['pk'])
        downloads = version.get_downloads(pretty=True)
        return Response({
            'downloads': downloads
        })

TEMPLATE = """
<div class="injected">

  {% if not new_theme %}
  <div class="rst-versions rst-badge" data-toggle="rst-versions">
    <span class="rst-current-version" data-toggle="rst-current-version">
      <span class="icon icon-book">&nbsp;</span>
      v: {{ current_version }}
      <span class="icon icon-caret-down"></span>
    </span>
    <div class="rst-other-versions">
  {% endif %}
  
      <dl>
        <dt>Versions</dt>
        {% for version in versions %}
          {% if version.slug == current_version %}
          <strong>
          {% endif %}
          <dd><a href="{{ version.get_subdomain_url }}">{{ version.slug }}</a></dd>
          {% if version.slug == current_version %}
          </strong>
          {% endif %}
        {% endfor %}
      </dl>
      <dl>
        <dt>Downloads</dt>
        {% for name, url in downloads.items %}
          <dd><a href="{{ url }}">{{ name }}</a></dd>
        {% endfor %}
      </dl>
      <dl>
        <dt>On Read the Docs</dt>
          <dd>
            <a href="//{{ settings.PRODUCTION_DOMAIN }}/projects/{{ project.slug }}/?fromdocs={{ project.slug }}">Project Home</a>
          </dd>
          <dd>
            <a href="//{{ settings.PRODUCTION_DOMAIN }}/builds/{{ project.slug }}/?fromdocs={{ project.slug }}">Builds</a>
          </dd>
      </dl>
      <hr/>
      Free document hosting provided by <a href="http://www.readthedocs.org">Read the Docs</a>.

  {% if not new_theme %}
    </div>
  </div>
  {% endif %}

</div>
"""

@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def footer_html(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', None)
    theme = request.GET.get('theme', False)
    new_theme = (theme == "sphinx_rtd_theme")
    using_theme = (theme == "default")
    project = get_object_or_404(Project, slug=project_slug)
    version = project.versions.get(slug=version_slug)
    context = Context({
        'project': project,
        'downloads': version.get_downloads(pretty=True),
        'current_version': version.slug,
        'versions': project.ordered_active_versions(),
        'using_theme': using_theme,
        'new_theme': new_theme,
        'settings': settings,
    })
    html = Template(TEMPLATE).render(context)
    return Response({"html": html})

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

@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def search(request):
    project_id = request.GET.get('project', None)
    version_slug = request.GET.get('version', 'latest')
    query = request.GET.get('q', None)

    if project_id:
        # This is a search within a project -- do a Page search.
        body = {
            'filter': {
                'term': {'project': project_id},
                'term': {'version': version_slug},
            },
            'query': {
                'bool': {
                    'should': [
                        {'match': {'title': {'query': query, 'boost': 10}}},
                        {'match': {'headers': {'query': query, 'boost': 5}}},
                        {'match': {'content': {'query': query}}},
                    ]
                }
            }
        }
        results = PageIndex().search(body, routing=project_id)

    else:
        body = {
            'query': {
                'bool': {
                    'should': [
                        {'match': {'name': {'query': query, 'boost': 10}}},
                        {'match': {'description': {'query': query}}},
                    ]
                }
            }
        }
        results = ProjectIndex().search(body)

    return Response({'results': results})
