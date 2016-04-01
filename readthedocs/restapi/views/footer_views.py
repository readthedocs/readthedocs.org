from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader as template_loader
from django.conf import settings

from rest_framework import decorators, permissions
from rest_framework.renderers import JSONPRenderer, JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Version
from readthedocs.donate.models import SupporterPromo
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import highest_version
from readthedocs.projects.version_handling import parse_version_failsafe


def get_version_compare_data(project, base_version=None):
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


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer))
def footer_html(request, redis=False):
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
    version = get_object_or_404(
        Version.objects.public(request.user, project=project, only_active=False),
        slug=version_slug)
    main_project = project.main_language_project or project

    if page_slug and page_slug != "index":
        if (
                main_project.documentation_type == "sphinx_htmldir" or
                main_project.documentation_type == "mkdocs"):
            path = page_slug + "/"
        elif main_project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + page_slug
        else:
            path = page_slug + ".html"
    else:
        path = ""

    if version.type == TAG and version.project.has_pdf(version.slug):
        print_url = (
            'https://keminglabs.com/print-the-docs/quote?project={project}&version={version}'
            .format(
                project=project.slug,
                version=version.slug))
    else:
        print_url = None

    use_promo = getattr(settings, 'USE_PROMOS', True)
    show_promo = project.allow_promos
    gold_user = gold_project = False
    promo_obj = None

    # User is a gold user, no promos for them!
    if request.user.is_authenticated():
        if request.user.gold.count() or request.user.goldonce.count():
            gold_user = True
    # A GoldUser has mapped this project
    if project.gold_owners.count():
        gold_project = True

    if gold_user or gold_project:
        show_promo = False

    if use_promo and show_promo:
        promo_obj = (SupporterPromo.objects
                     .filter(live=True, display_type='doc')
                     .order_by('?')
                     .first())

        # Support showing a "Thank you" message for gold folks
        if gold_user:
            gold_promo = SupporterPromo.objects.filter(live=True,
                                                       name='gold-user')
            if gold_promo.exists():
                promo_obj = gold_promo.first()

        # Default to showing project-level thanks if it exists
        if gold_project:
            gold_promo = SupporterPromo.objects.filter(live=True,
                                                       name='gold-project')
            if gold_promo.exists():
                promo_obj = gold_promo.first()

        if not promo_obj:
            show_promo = False

    version_compare_data = get_version_compare_data(project, version)

    context = {
        'project': project,
        'version': version,
        'path': path,
        'downloads': version.get_downloads(pretty=True),
        'current_version': version.verbose_name,
        'versions': project.ordered_active_versions(user=request.user),
        'main_project': main_project,
        'translations': main_project.translations.all(),
        'current_language': project.language,
        'using_theme': using_theme,
        'new_theme': new_theme,
        'settings': settings,
        'subproject': subproject,
        'print_url': print_url,
        'github_edit_url': version.get_github_url(docroot, page_slug, source_suffix, 'edit'),
        'github_view_url': version.get_github_url(docroot, page_slug, source_suffix, 'view'),
        'bitbucket_url': version.get_bitbucket_url(docroot, page_slug, source_suffix),
    }

    request_context = RequestContext(request, context)
    html = template_loader.get_template('restapi/footer.html').render(request_context)
    resp_data = {
        'html': html,
        'version_active': version.active,
        'version_compare': version_compare_data,
        'version_supported': version.supported,
        'promo': show_promo,
    }
    if show_promo and promo_obj:
        resp_data['promo_data'] = promo_obj.as_dict()
        if redis:
            promo_obj.incr('offers')
        else:
            promo_obj.incr_redis('offers')
    return Response(resp_data)
