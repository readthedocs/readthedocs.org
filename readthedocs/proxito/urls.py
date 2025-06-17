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

from functools import reduce
from operator import add

from django.conf import settings
from django.urls import include
from django.urls import path
from django.urls import re_path

from readthedocs.constants import pattern_opts
from readthedocs.core.views import HealthCheckView
from readthedocs.projects.views.public import ProjectDownloadMedia
from readthedocs.proxito.views.hosting import ReadTheDocsConfigJson
from readthedocs.proxito.views.serve import ServeDocs
from readthedocs.proxito.views.serve import ServeError404
from readthedocs.proxito.views.serve import ServePageRedirect
from readthedocs.proxito.views.serve import ServeRobotsTXT
from readthedocs.proxito.views.serve import ServeSitemapXML
from readthedocs.proxito.views.serve import ServeStaticFiles
from readthedocs.proxito.views.utils import ProxitoErrorView
from readthedocs.proxito.views.utils import proxito_404_page_handler


DOC_PATH_PREFIX = getattr(settings, "DOC_PATH_PREFIX", "")

health_check_urls = [
    re_path(
        "^{DOC_PATH_PREFIX}health_check/$".format(DOC_PATH_PREFIX=DOC_PATH_PREFIX),
        HealthCheckView.as_view(),
        name="health_check",
    ),
]

proxied_urls = [
    # Serve project downloads
    # /_/downloads/<lang>/<ver>/<type>/
    re_path(
        (
            r"^{DOC_PATH_PREFIX}downloads/"
            r"(?P<lang_slug>{lang_slug})/"
            r"(?P<version_slug>{version_slug})/"
            r"(?P<type_>{downloadable_type})/$".format(
                DOC_PATH_PREFIX=DOC_PATH_PREFIX, **pattern_opts
            )
        ),
        ProjectDownloadMedia.as_view(same_domain_url=True),
        name="project_download_media",
    ),
    # Serve subproject downloads
    # /_/downloads/<alias>/<lang>/<ver>/<type>/
    re_path(
        (
            r"^{DOC_PATH_PREFIX}downloads/"
            r"(?P<subproject_slug>{project_slug})/"
            r"(?P<lang_slug>{lang_slug})/"
            r"(?P<version_slug>{version_slug})/"
            r"(?P<type_>{downloadable_type})/$".format(
                DOC_PATH_PREFIX=DOC_PATH_PREFIX, **pattern_opts
            )
        ),
        ProjectDownloadMedia.as_view(same_domain_url=True),
        name="project_download_media",
    ),
    # Serve proxied API
    # /_/api/v2/
    re_path(
        r"^{DOC_PATH_PREFIX}api/v2/".format(
            DOC_PATH_PREFIX=DOC_PATH_PREFIX,
        ),
        include("readthedocs.api.v2.proxied_urls"),
    ),
    # /_/api/v3/
    re_path(
        r"^{DOC_PATH_PREFIX}api/v3/".format(
            DOC_PATH_PREFIX=DOC_PATH_PREFIX,
        ),
        include("readthedocs.api.v3.proxied_urls"),
    ),
    # Serve static files
    # /_/static/file.js
    path(
        f"{DOC_PATH_PREFIX}static/<path:filename>",
        ServeStaticFiles.as_view(),
        name="proxito_static_files",
    ),
    # readthedocs-docs-addons.js
    path(
        f"{DOC_PATH_PREFIX}addons/",
        ReadTheDocsConfigJson.as_view(),
        name="proxito_readthedocs_docs_addons",
    ),
]

core_urls = [
    # Serve custom 404 pages
    re_path(
        r"^_proxito_404_(?P<proxito_path>.*)$",
        ServeError404.as_view(),
        name="proxito_404_handler",
    ),
    re_path(r"robots\.txt$", ServeRobotsTXT.as_view(), name="robots_txt"),
    re_path(r"sitemap\.xml$", ServeSitemapXML.as_view(), name="sitemap_xml"),
]

docs_urls = [
    # # TODO: Support this?
    # (Sub)project `page` redirect
    re_path(
        r"^(?:projects/(?P<subproject_slug>{project_slug})/)?"
        r"page/(?P<filename>.*)$".format(**pattern_opts),
        ServePageRedirect.as_view(),
        name="redirect_page_with_filename",
    ),
    re_path(r"^(?P<path>.*)$", ServeDocs.as_view(), name="docs_detail"),
]


# Declare dummy "dashboard URLs" in El Proxito to be able to ``reverse()`` them
# from API ``/_/addons/`` endpoint. Mainly for the the ``*.urls`` fields. We
# cannot resolve ``*._links`` fields properly yet, but they are not required at
# this point. We can come back later here if we need them.
# See https://github.com/readthedocs/readthedocs-ops/issues/1323
dummy_dashboard_urls = [
    # /projects/<project_slug>/
    re_path(
        r"^projects/(?P<project_slug>{project_slug})/$".format(**pattern_opts),
        ProxitoErrorView.as_view(status_code=418),
        name="projects_detail",
    ),
    # /projects/<project_slug>/builds/
    re_path(
        (r"^projects/(?P<project_slug>{project_slug})/builds/$".format(**pattern_opts)),
        ProxitoErrorView.as_view(status_code=418),
        name="builds_project_list",
    ),
    # /projects/<project_slug>/versions/
    re_path(
        r"^projects/(?P<project_slug>{project_slug})/versions/$".format(**pattern_opts),
        ProxitoErrorView.as_view(status_code=418),
        name="project_version_list",
    ),
    # /projects/<project_slug>/builds/<build_id>/
    re_path(
        (
            r"^projects/(?P<project_slug>{project_slug})/builds/(?P<build_pk>\d+)/$".format(
                **pattern_opts
            )
        ),
        ProxitoErrorView.as_view(status_code=418),
        name="builds_detail",
    ),
    # /projects/<project_slug>/version/<version_slug>/
    re_path(
        r"^projects/(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/edit/$",
        ProxitoErrorView.as_view(status_code=418),
        name="project_version_detail",
    ),
]

debug_urls = [
    # For testing error responses and templates
    re_path(
        r"^{DOC_PATH_PREFIX}error/(?P<template_name>.*)$".format(
            DOC_PATH_PREFIX=DOC_PATH_PREFIX,
        ),
        ProxitoErrorView.as_view(),
    ),
]

groups = [
    health_check_urls,
    proxied_urls,
    core_urls,
    docs_urls,
    # Fallback paths only required for resolving URLs, evaluate these last
    dummy_dashboard_urls,
]

if settings.SHOW_DEBUG_TOOLBAR:
    groups.insert(0, debug_urls)

urlpatterns = reduce(add, groups)

# Use Django default error handlers to make things simpler
handler404 = proxito_404_page_handler
handler500 = ProxitoErrorView.as_view(status_code=500)
