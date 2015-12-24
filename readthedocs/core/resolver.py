"""
Read the Docs URL Resolver.

Url Types:

- Subdomain
- CNAME

Path Types:

- Subproject
- Single Version
- Normal

All possible URL's::

    Subdomain or CNAME:

    /<lang>/<version>/<filename> # Default
    /<filename> # Single Version
    /projects/<subproject_slug>/<lang>/<version>/<filename> # Subproject Default
    /projects/<subproject_slug>/<filename> # Subproject Single Version

    Normal Serving:

    /docs/<project_slug>/<lang>/<version>/<filename> # Default
    /docs/<project_slug>/<filename> # Single Version
    /docs/<project_slug>/projects/<subproject_slug>/<lang>/<version>/<filename> # Subproject Default
    /docs/<project_slug>/projects/<subproject_slug>/<filename> # Subproject Single Version
"""

import re

from django.conf import settings

from readthedocs.projects.constants import PRIVATE, PUBLIC


def _get_private(project, version_slug):
    from readthedocs.builds.models import Version
    try:
        version = project.versions.get(slug=version_slug)
        private = version.privacy_level == PRIVATE
    except Version.DoesNotExist:
        private = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', PUBLIC) == PRIVATE
    return private


def _fix_filename(project, filename):
    """
    Force filenames that might be HTML file paths into proper URL's

    This basically means stripping / and .html endings and then re-adding them properly.
    """
    filename = filename.lstrip('/')
    filename = re.sub('index.html$', '', filename)
    filename = re.sub('index$', '', filename)
    if filename:
        if filename.endswith('/') or filename.endswith('.html'):
            path = filename
        elif project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + filename
        elif project.documentation_type in ["sphinx_htmldir", "mkdocs"]:
            path = filename + "/"
        else:
            path = filename + ".html"
    else:
        path = ""
    return path


def base_resolve_path(project_slug, filename, version_slug=None, language=None, private=False,
                      single_version=None, subproject_slug=None,  subdomain=None, cname=None):
    """ Resolve a with nothing smart, just filling in the blanks."""

    if private:
        url = '/docs/{project_slug}/'
    elif subdomain or cname:
        url = '/'
    else:
        url = '/docs/{project_slug}/'

    if subproject_slug:
        url += 'projects/{subproject_slug}/'

    if single_version:
        url += '{filename}'
    else:
        url += '{language}/{version_slug}/{filename}'

    return url.format(
        project_slug=project_slug, filename=filename,
        version_slug=version_slug, language=language,
        single_version=single_version, subproject_slug=subproject_slug,
    )


def resolve_path(project, filename='', version_slug=None, language=None,
                 single_version=None, subdomain=None, cname=None, private=None):
    """ Resolve a URL with a subset of fields defined."""
    subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    relation = project.superprojects.first()
    cname = cname or project.domains.filter(canonical=True).first()
    main_language_project = project.main_language_project

    version_slug = version_slug or project.get_default_version()
    language = language or project.language

    if private is None:
        private = _get_private(project, version_slug)

    filename = _fix_filename(project, filename)

    if main_language_project:
        project_slug = main_language_project.slug
        language = project.language
        subproject_slug = None
    elif relation:
        project_slug = relation.parent.slug
        subproject_slug = relation.alias
        cname = relation.parent.domains.filter(canonical=True).first()
    else:
        project_slug = project.slug
        subproject_slug = None

    if project.single_version or single_version:
        single_version = True
    else:
        single_version = False

    return base_resolve_path(project_slug=project_slug, filename=filename,
                             version_slug=version_slug, language=language,
                             single_version=single_version, subproject_slug=subproject_slug,
                             subdomain=subdomain, cname=cname, private=private)


def resolve_domain(project, private=None):
    main_language_project = project.main_language_project
    relation = project.superprojects.first()
    subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    prod_domain = getattr(settings, 'PRODUCTION_DOMAIN')
    public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)

    if public_domain is None:
        public_domain = prod_domain
    if private is None:
        private = project.privacy_level == PRIVATE

    if main_language_project:
        canonical_project = main_language_project
    elif relation:
        canonical_project = relation.parent
    else:
        canonical_project = project

    domain = canonical_project.domains.filter(canonical=True).first()
    # Force domain even if USE_SUBDOMAIN is on
    if domain:
        return domain.domain
    elif subdomain:
        subdomain_slug = canonical_project.slug.replace('_', '-')
        return "%s.%s" % (subdomain_slug, public_domain)
    else:
        return public_domain


def resolve(project, protocol='http', filename='', private=None, **kwargs):
    if private is None:
        version_slug = kwargs.get('version_slug')
        if version_slug is None:
            version_slug = project.get_default_version()
        private = _get_private(project, version_slug)

    return '{protocol}://{domain}{path}'.format(
        protocol=protocol,
        domain=resolve_domain(project, private=private),
        path=resolve_path(project, filename=filename, private=private, **kwargs),
    )
