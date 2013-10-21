from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.conf import settings

from distlib.version import UnsupportedVersionError
from rest_framework import decorators
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from betterversion.better import version_windows, BetterVersion 
from builds.models import Version
from projects.models import Project, EmailHook

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
            return Response({'error': 'Project does not support point version control.'})
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

    @link()
    def downloads(self, request, **kwargs):
        version = get_object_or_404(Version, pk=kwargs['pk'])
        downloads = version.get_downloads(pretty=True)
        return Response({
            'downloads': downloads
        })

TEMPLATE = """
 <!-- End original user content -->
{% if not using_theme %}
<br/>
<br/>
<br/>
{% endif %}

<style type="text/css">
  #version_menu, .rtd-badge.rtd {
    -webkit-transition: all 0.25s 0.75s;
    transition: all 0.25s 0.75s;
  }
  .footer_popout:hover #version_menu, .footer_popout:hover .rtd-badge.rtd {
    -webkit-transition: all 0.25s 0s;
    transition: all 0.25s 0s;
  }
  .rtd-badge {
    position: fixed;
    display: block;
    bottom: 5px;
    height: 40px;
    text-indent: -9999em;
    border-radius: 3px;
    -moz-border-radius: 3px;
    -webkit-border-radius: 3px;
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset;
    -moz-box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset;
    -webkit-box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2), 0 1px 0 rgba(255, 255, 255, 0.2) inset;
  }
  #version_menu {
    position: fixed;
    visibility: hidden;
    opacity: 0;
    bottom: 11px;
    right: 47px;
    list-style-type: none;
    margin: 0;
  }
  .footer_popout:hover #version_menu {
    visibility: visible;
    opacity: 1;
    right: 166px;
  }
  #version_menu li {
    display: block;
    float: right;
  }
  #version_menu li a {
    display: block;
    padding: 6px 10px 4px 10px;
    margin: 7px 7px 0 0;
    font-weight: bold;
    font-size: 14px;
    height: 20px;
    line-height: 17px;
    text-decoration: none;
    color: #fff;
    background: #8ca1af url({{ settings.MEDIA_URL }}/images/gradient-light.png) bottom left repeat-x;
    border-radius: 3px;
    -moz-border-radius: 3px;
    -webkit-border-radius: 3px;
    box-shadow: 0 1px 1px #465158;
    -moz-box-shadow: 0 1px 1px #465158;
    -webkit-box-shadow: 0 1px 1px #465158;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.5);
  }
  #version_menu li a:hover {
    text-decoration: none;
    background-color: #697983;
    box-shadow: 0 1px 0px #465158;
    -moz-box-shadow: 0 1px 0px #465158;
    -webkit-box-shadow: 0 1px 0px #465158;
  }
  .rtd-badge.rtd {
    background: #3b4449 url({{ settings.MEDIA_URL }}/images/badge-rtd.png) scroll top left no-repeat;
    border: 1px solid #282E32;
    width: 41px;
    right: 5px;
  }
  .footer_popout:hover .rtd-badge.rtd {
    width: 160px;
  }
  .rtd-badge.revsys { background: #465158 url({{ settings.MEDIA_URL }}/images/badge-revsys.png) top left no-repeat;
    border: 1px solid #1C5871;
    width: 290px;
    right: 173px;
  }
  .rtd-badge.revsys-inline-sponsored {
    position: inherit;
    margin-left: auto;
    margin-right: 175px;
    margin-bottom: 5px;
    background: #465158 url({{ settings.MEDIA_URL }}/images/badge-revsys.png) top left no-repeat;
    border: 1px solid #1C5871;
    width: 290px;
    right: 173px;
  }
  .rtd-badge.revsys-inline {
    position: inherit;
    margin-left: auto;
    margin-right: 175px;
    margin-bottom: 5px;
    background: #465158 url({{ settings.MEDIA_URL }}/images/badge-revsys-sm.png) top left no-repeat;
    border: 1px solid #1C5871;
    width: 205px;
    right: 173px;
  }

{% if using_theme %}
.rtd_doc_footer { background-color: #465158;}
{% endif %}
</style>

<div class="rtd_doc_footer">
  <div class="footer_popout">
    <a href="//{{ settings.PRODUCTION_DOMAIN }}/projects/{{ project.slug }}/?fromdocs={{ project.slug }}" class="rtd-badge rtd"> Brought to you by Read the Docs</a>
  </div>
</div>

{% if project.analytics_code %}
<!-- User Analytics Code -->
<script type="text/javascript">
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', '{{ project.analytics_code }}']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
</script>
{% endif %}
"""

@decorators.api_view(['GET'])
def footer_html(request):
    slug = request.GET.get('project', None)
    using_theme = request.GET.get('using_theme', False)
    project = get_object_or_404(Project, slug=slug)
    context = Context({
        'project': project.slug,
        'using_theme': using_theme,
        'settings': settings,
    })
    html = Template(TEMPLATE).render(context)
    return Response({"html": html})
