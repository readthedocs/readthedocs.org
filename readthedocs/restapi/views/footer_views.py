from django.shortcuts import get_object_or_404
from django.template import Context, loader as template_loader
from django.conf import settings

from rest_framework import decorators, permissions, viewsets, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from projects.models import Project

@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def footer_html(request):
    project_slug = request.GET.get('project', None)
    version_slug = request.GET.get('version', None)
    page_slug = request.GET.get('page', None)
    theme = request.GET.get('theme', False)
    docroot = request.GET.get('docroot', '')
    subproject = request.GET.get('subproject', False)
    source_suffix = request.GET.get('source_suffix', '.rst')

    new_theme = (theme == "sphinx_rtd_theme")
    using_theme = (theme == "default")
    project = get_object_or_404(Project, slug=project_slug)
    version = get_object_or_404(project.versions.all(), slug=version_slug)
    main_project = project.main_language_project or project

    if page_slug and page_slug != "index":
        if main_project.documentation_type == "sphinx_htmldir" or main_project.documentation_type == "mkdocs":
            path =  page_slug + "/"
        elif main_project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + page_slug
        else:
            path =  page_slug + ".html"
    else:
        path = ""

    context = Context({
        'project': project,
        'path': path,
        'downloads': version.get_downloads(pretty=True),
        'current_version': version.slug,
        'versions': project.ordered_active_versions(),
        'main_project': main_project,
        'translations': main_project.translations.all(),
        'current_language': project.language,
        'using_theme': using_theme,
        'new_theme': new_theme,
        'settings': settings,
        'subproject': subproject,
        'github_edit_url': version.get_github_url(docroot, page_slug, source_suffix, 'edit'),
        'github_view_url': version.get_github_url(docroot, page_slug, source_suffix, 'view'),
        'bitbucket_url': version.get_bitbucket_url(docroot, page_slug, source_suffix),
    })

    html = template_loader.get_template('restapi/footer.html').render(context)
    return Response({
        'html': html, 
        'version_active': version.active,
        'version_supported': version.supported,
    })
