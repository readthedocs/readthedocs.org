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

## Proxied API

pip.rtd.io/_/api/*
"""

from django.conf import settings
from django.conf.urls import include, url
from django.views import defaults

from readthedocs.constants import pattern_opts
from readthedocs.projects.views.public import ProjectDownloadMedia
from readthedocs.proxito.views.serve import (
    ServeDocs,
    ServeError404,
    ServePageRedirect,
    ServeRobotsTXT,
    ServeSitemapXML,
)
from readthedocs.proxito.views.utils import proxito_404_page_handler, fast_404

DOC_PATH_PREFIX = getattr(settings, 'DOC_PATH_PREFIX', '')

proxied_urls = [
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

    # Serve proxied API
    # /_/api/v2/
    url(
        r'^{DOC_PATH_PREFIX}api/v2/'.format(
            DOC_PATH_PREFIX=DOC_PATH_PREFIX,
        ),
        include('readthedocs.api.v2.proxied_urls'),
    ),
]

core_urls = [
    # Serve custom 404 pages
    url(
        r'^_proxito_404_(?P<proxito_path>.*)$',
        ServeError404.as_view(),
        name='proxito_404_handler',
    ),
    url(r'robots\.txt$', ServeRobotsTXT.as_view(), name='robots_txt'),
    url(r'sitemap\.xml$', ServeSitemapXML.as_view(), name='sitemap_xml'),
]

docs_urls = [

    # # TODO: Support this?
    # (Sub)project `page` redirect
    url(
        r'^(?:projects/(?P<subproject_slug>{project_slug})/)?'
        r'page/(?P<filename>.*)$'.format(**pattern_opts),
        ServePageRedirect.as_view(),
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

    # Hack /en/latest so it redirects properly
    # We don't want to serve the docs here,
    # because it's at a different level of serving so relative links break.
    url(
        (
            r'^(?:projects/(?P<subproject_slug>{project_slug})/)?'
            r'(?P<lang_slug>{lang_slug})/'
            r'(?P<version_slug>{version_slug})$'.format(**pattern_opts)
        ),
        fast_404,
        name='docs_detail_directory_indexing',
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

    # (Sub)project single version
    url(
        (
            # subproject_slash variable at the end of this regex is for ``/projects/subproject``
            # so that it will get captured here and redirect properly.
            r'^(?:projects/(?P<subproject_slug>{project_slug})(?P<subproject_slash>/?))?'
            r'(?P<filename>{filename_slug})$'.format(**pattern_opts)
        ),
        ServeDocs.as_view(),
        name='docs_detail_singleversion_subproject',
    ),
]

urlpatterns = proxied_urls + core_urls + docs_urls

# Use Django default error handlers to make things simpler
handler404 = proxito_404_page_handler
handler500 = defaults.server_error
