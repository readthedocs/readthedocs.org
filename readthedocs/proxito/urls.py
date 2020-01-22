"""
A quick rundown of all the URL's we are hoping to parse.

## Projects

pip.rtfd.io/<lang>/<version>/

* Can be single version (pip.rtfd.io/index.html)
* Can be translated (pip.rtfd.io/cz/latest/index.html)
* Can have subprojects (pip.rtfd.io/projects/foo/en/latest/index.html)

## Subprojects

pip.rtfd.io/projects/<slug>/

* Can be single version (pip.rtfd.io/projects/subproject/index.html)
* Can be translated (pip.rtfd.io/projects/subproject/cz/latest/index.html)
* Can't have subprojects (pip.rtfd.io/projects/foo/projects/bar/en/latest/index.html)

## Translations

pip.rtfd.io/<lang>/

* Must be served directly (pip.rtfd.io/cz/latest/index.html)
* Can't be single version (pip.rtfd.io/en/index.html)
    * TODO: Possibly support this, it seems reasonable
* Can't have subprojects (pip.rtfd.io/en/projects/foo/en/latestindex.html)
    * This would stop us from detaching translations from Project modeling
* Can't be translated (pip.rtfd.io/cz/en/latest/index.html)
"""

from django.conf import settings
from django.conf.urls import url
from django.views import defaults

from readthedocs.constants import pattern_opts
from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.views.public import ProjectDownloadMedia
from readthedocs.proxito.views.serve import (
    ServeDocs,
    ServeError404,
    ServeRobotsTXT,
    ServeSitemapXML,
)
from readthedocs.proxito.views.redirects import redirect_page_with_filename
from readthedocs.proxito.views.utils import fast_404

DOC_PATH_PREFIX = getattr(settings, 'DOC_PATH_PREFIX', '')

urlpatterns = [
    # Serve project downloads
    # /_/downloads/<lang>/<ver>/<type>/
    url(
        (
            r'^{DOC_PATH_PREFIX}downloads/'
            r'(?P<lang_slug>{lang_slug})/'
            r'(?P<version_slug>{version_slug})/'
            r'(?P<type_>[-\w]+)/$'.format(
                DOC_PATH_PREFIX=DOC_PATH_PREFIX,
                **pattern_opts)
        ),
        ProjectDownloadMedia.as_view(same_domain_url=True),
        name='project_download_media',
    ),
    # Serve subproject downloads
    # /_/downloads/<alias>/<lang>/<ver>/<type>/
    url(
        (
            r'^{DOC_PATH_PREFIX}downloads/'
            r'(?P<subproject_slug>{project_slug})/'
            r'(?P<lang_slug>{lang_slug})/'
            r'(?P<version_slug>{version_slug})/'
            r'(?P<type_>[-\w]+)/$'.format(
                DOC_PATH_PREFIX=DOC_PATH_PREFIX,
                **pattern_opts)
        ),
        ProjectDownloadMedia.as_view(same_domain_url=True),
        name='project_download_media',
    ),

    # Serve custom 404 pages
    url(
        r'^_proxito_404_(?P<proxito_path>.*)$',
        ServeError404.as_view(),
        name='serve_error_404',
    ),
    url(r'robots\.txt$', ServeRobotsTXT.as_view(), name='robots_txt'),
    url(r'sitemap\.xml$', ServeSitemapXML.as_view(), name='sitemap_xml'),

    # # TODO: Support this?
    # (Sub)project `page` redirect
    url(
        r'^(?:projects/(?P<subproject_slug>{project_slug})/)?'
        r'page/(?P<filename>.*)$'.format(**pattern_opts),
        redirect_page_with_filename,
        name='redirect_page_with_filename',
    ),

    # (Sub)project w/ translation and versions
    url(
        (
            r'^(?:projects/(?P<subproject_slug>{project_slug})/)?'
            r'(?P<lang_slug>{lang_slug})/'
            r'(?P<version_slug>{version_slug})/'
            r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
        ),
        ServeDocs.as_view(),
        name='docs_detail',
    ),

    # # TODO: Support this?
    # # (Sub)project translation and single version
    # url(
    #     (
    #         r'^(?:|projects/(?P<subproject_slug>{project_slug})/)'
    #         r'(?P<lang_slug>{lang_slug})/'
    #         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
    #     ),
    #     serve_docs,
    #     name='docs_detail',
    # ),

    # External versions
    # (RTD_EXTERNAL_VERSION_DOMAIN/html/<project-slug>/<version-slug>/<filename>)
    # NOTE: requires to be before single version
    url(
        (
            r'^html/(?P<project_slug>{project_slug})/'
            r'(?P<version_slug>{version_slug})/'
            r'(?P<filename>{filename_slug})'.format(
                **pattern_opts,
            )
        ),
        ServeDocs.as_view(version_type=EXTERNAL),
        name='docs_detail_external_version',
    ),

    # (Sub)project single version
    url(
        (
            r'^(?:projects/(?P<subproject_slug>{project_slug})/)?'
            r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
        ),
        ServeDocs.as_view(),
        name='docs_detail_singleversion_subproject',
    ),
]

# Use Django default error handlers to make things simpler
# handler404 = fast_404

# Allow performing NGINX internal redirects at Django level.
# This is useful for testing El Proxito ``@notfoundfallback``
# TODO: move this to a proper place
from functools import wraps
def map_proxito_path(view_func):

    @wraps(view_func)
    def inner_view(request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        return view_func(
            request,
            *args,
            proxito_path=request.get_full_path(),
            **kwargs,
        )
    return inner_view

handler404 = map_proxito_path(ServeError404.as_view())

handler500 = defaults.server_error
