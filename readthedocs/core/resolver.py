"""
Read the Docs URL Resolver.

Url Types:

- Subproject
- Subdomain
- CNAME
- Single Version
- Normal

All possible URL's::

    Subdomain or CNAME:

    /<lang>/<version>/<filename> # Default
    /<filename> # Single Version
    /projects/<subproject_slug>/<lang>/<version>/<filename> # Subproject
    /projects/<subproject_slug>/<filename> # Subproject Single Version

    Normal Serving:

    /docs/<project_slug>/<lang>/<version>/<filename> # Default
    /docs/<project_slug>/<filename> # Single Version
    /docs/<project_slug>/projects/<subproject_slug>/<lang>/<version>/<filename> # Subproject
    /docs/<project_slug>/projects/<subproject_slug>/<filename> # Subproject Single Version
"""

from django.conf import settings


def base_resolve(project_slug, filename, version_slug=None, language=None,
                 single_version=None, subproject_slug=None,  subdomain=None, cname=None):
    """ Resolve a with nothing smart, just filling in the blanks."""
    filename = filename.lstrip('/')

    if subdomain or cname:
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


def resolve(project, filename='', version_slug=None, language=None,
            single_version=None, subdomain=None, cname=None):
    """ Resolve a URL with a subset of fields defined."""
    subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    relation = project.superprojects.first()
    cname = cname or project.domains.first()
    main_language_project = project.main_language_project

    version_slug = version_slug or project.get_default_version()
    language = language or project.language

    if main_language_project:
        project_slug = main_language_project.slug
        language = project.language
        subproject_slug = None
    elif relation:
        project_slug = relation.parent.slug
        subproject_slug = relation.child.slug
    else:
        project_slug = project.slug
        subproject_slug = None

    if project.single_version or single_version:
        single_version = True
    else:
        single_version = False

    return base_resolve(project_slug=project_slug, filename=filename,
                        version_slug=version_slug, language=language,
                        single_version=single_version, subproject_slug=subproject_slug,
                        subdomain=subdomain, cname=cname)


def smart_resolve(project, filename=''):
    """ Resolve a URL with all fields automatically filled in from the project."""
    subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
    relation = project.superprojects.first()
    cname = project.domains.first()
    main_language_project = project.main_language_project

    version_slug = project.get_default_version()
    language = project.language

    if main_language_project:
        project_slug = main_language_project.slug
        language = project.language
        subproject_slug = None
    elif relation:
        project_slug = relation.parent.slug
        subproject_slug = relation.child.slug
    else:
        project_slug = project.slug
        subproject_slug = None

    if project.single_version:
        single_version = True
    else:
        single_version = False

    return base_resolve(project_slug=project_slug, filename=filename,
                        version_slug=version_slug, language=language,
                        single_version=single_version, subproject_slug=subproject_slug,
                        subdomain=subdomain, cname=cname)
