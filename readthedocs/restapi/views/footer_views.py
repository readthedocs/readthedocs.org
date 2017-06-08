"""Endpoint to generate footer HTML."""
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader as template_loader
from django.conf import settings


from rest_framework import decorators, permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_jsonp.renderers import JSONPRenderer

from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import highest_version
from readthedocs.projects.version_handling import parse_version_failsafe
from readthedocs.restapi.signals import footer_response


def get_version_compare_data(project, base_version=None):
    """Retrieve metadata about the highest version available for this project.

    :param base_version: We assert whether or not the base_version is also the
                         highest version in the resulting "is_highest" value.
    """
    highest_version_obj, highest_version_comparable = highest_version(
        project.versions.public().filter(active=True))
    ret_val = {
        'project': unicode(highest_version_obj),
        'version': unicode(highest_version_comparable),
        'is_highest': True,
    }
    if highest_version_obj:
        ret_val['url'] = highest_version_obj.get_absolute_url()
        ret_val['slug'] = highest_version_obj.slug,
    if base_version and base_version.slug != LATEST:
        try:
            base_version_comparable = parse_version_failsafe(
                base_version.verbose_name)
            if base_version_comparable:
                # This is only place where is_highest can get set. All error
                # cases will be set to True, for non- standard versions.
                ret_val['is_highest'] = (
                    base_version_comparable >= highest_version_comparable)
            else:
                ret_val['is_highest'] = True
        except (Version.DoesNotExist, TypeError):
            ret_val['is_highest'] = True
    return ret_val


def footer_path(main_project, page_slug):
    if page_slug and page_slug != "index":
        if main_project.documentation_type in ("sphinx_htmldir", "mkdocs"):
            return page_slug + "/"
        elif main_project.documentation_type == "sphinx_singlehtml":
            return "index.html#document-" + page_slug
        else:
            return page_slug + ".html"
    else:
        return ""


def version_context(project, request):
    """Derive extra footer context by looking up the requested version."""
    page_slug = request.GET.get('page')
    version_slug = request.GET.get('version')
    docroot = request.GET.get('docroot', '')
    source_suffix = request.GET.get('source_suffix', '.rst')
    main_project = project.main_language_project or project

    version = get_object_or_404(
        Version.objects.public(request.user, project=project, only_active=False),
        slug=version_slug)

    if version.type == TAG and version.project.has_pdf(version.slug):
        print_url = (
            'https://keminglabs.com/print-the-docs/quote?project={project}&version={version}'
            .format(
                project=project.slug,
                version=version.slug))
    else:
        print_url = None

    return {
        'version': version,
        'path': footer_path(main_project, page_slug),
        'downloads': version.get_downloads(pretty=True),
        'main_project': main_project,
        'translations': main_project.translations.all(),
        'current_version': version.verbose_name,
        'print_url': print_url,
        'github_edit_url': version.get_github_url(docroot, page_slug, source_suffix, 'edit'),
        'github_view_url': version.get_github_url(docroot, page_slug, source_suffix, 'view'),
        'bitbucket_url': version.get_bitbucket_url(docroot, page_slug, source_suffix),
    }


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer))
def footer_html(request):
    """Render and return footer markup."""
    project_slug = request.GET.get('project', None)
    theme = request.GET.get('theme', False)
    subproject = request.GET.get('subproject', False)

    new_theme = (theme == "sphinx_rtd_theme")
    using_theme = (theme == "default")
    project = get_object_or_404(Project, slug=project_slug)

    context = {
        'project': project,
        'versions': project.ordered_active_versions(user=request.user),
        'current_language': project.language,
        'using_theme': using_theme,
        'new_theme': new_theme,
        'settings': settings,
        'subproject': subproject,
        'theme': theme,
    }
    context.update(version_context(project, request))

    request_context = RequestContext(request, context)
    html = template_loader.get_template('restapi/footer.html').render(request_context)
    version = context['version']
    resp_data = {
        'html': html,
        'version_active': version.active,
        'version_compare': get_version_compare_data(project, version),
        'version_supported': version.supported,
    }

    # Allow folks to hook onto the footer response for various information collection,
    # or to modify the resp_data.
    footer_response.send(sender=None, request=request, context=context, resp_data=resp_data)

    return Response(resp_data)
