"""URL resolver for documentation."""

import logging
from urllib.parse import urlunparse

from django.conf import settings

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.builds.constants import EXTERNAL

log = logging.getLogger(__name__)


class ResolverBase:

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

        # Default
        /<lang>/<version>/<filename>
        # Single Version
        /<filename>
        # Subproject Default
        /projects/<subproject_slug>/<lang>/<version>/<filename>
        # Subproject Single Version
        /projects/<subproject_slug>/<filename>

        Development serving:

        # Default
        /docs/<project_slug>/<lang>/<version>/<filename>
        # Single Version
        /docs/<project_slug>/<filename>
        # Subproject Default
        /docs/<project_slug>/projects/<subproject_slug>/<lang>/<version>/<filename>
        # Subproject Single Version
        /docs/<project_slug>/projects/<subproject_slug>/<filename>
    """

    def base_resolve_path(
            self,
            project_slug,
            filename,
            version_slug=None,
            language=None,
            single_version=None,
            subproject_slug=None,
            subdomain=None,
            cname=None,
            urlconf=None,
    ):
        """Resolve a with nothing smart, just filling in the blanks."""
        # Only support `/docs/project' URLs outside our normal environment. Normally
        # the path should always have a subdomain or CNAME domain
        if subdomain or cname or (self._use_subdomain()):
            url = '/'
        else:
            url = '/docs/{project_slug}/'

        if subproject_slug:
            url += 'projects/{subproject_slug}/'

        if single_version:
            url += '{filename}'
        else:
            url += '{language}/{version_slug}/{filename}'

        # Allow users to override their own URLConf
        # This logic could be cleaned up with a standard set of variable replacements
        if urlconf:
            url = urlconf
            url = url.replace(
                '$version',
                '{version_slug}',
            )
            url = url.replace(
                '$language',
                '{language}',
            )
            url = url.replace(
                '$filename',
                '{filename}',
            )
            url = url.replace(
                '$subproject',
                '{subproject_slug}',
            )
            if '$' in url:
                log.warning(
                    'Unconverted variable in a resolver URLConf: url=%s', url
                )

        return url.format(
            project_slug=project_slug,
            filename=filename,
            version_slug=version_slug,
            language=language,
            single_version=single_version,
            subproject_slug=subproject_slug,
        )

    def resolve_path(
            self,
            project,
            filename='',
            version_slug=None,
            language=None,
            single_version=None,
            subdomain=None,
            cname=None,
            urlconf=None,
    ):
        """Resolve a URL with a subset of fields defined."""
        version_slug = version_slug or project.get_default_version()
        language = language or project.language

        filename = self._fix_filename(project, filename)

        main_project, subproject_slug = self._get_canonical_project_data(project)
        project_slug = main_project.slug
        cname = (
            cname
            or self._use_subdomain()
            or main_project.get_canonical_custom_domain()
        )
        single_version = bool(project.single_version or single_version)

        return self.base_resolve_path(
            project_slug=project_slug,
            filename=filename,
            version_slug=version_slug,
            language=language,
            single_version=single_version,
            subproject_slug=subproject_slug,
            cname=cname,
            subdomain=subdomain,
            urlconf=urlconf or project.urlconf,
        )

    def resolve_domain(self, project):
        canonical_project = self._get_canonical_project(project)
        domain = canonical_project.get_canonical_custom_domain()
        if domain:
            return domain.domain

        if self._use_subdomain():
            return self._get_project_subdomain(canonical_project)

        return settings.PRODUCTION_DOMAIN

    def resolve(
            self, project, require_https=False, filename='', query_params='',
            external=None, **kwargs
    ):
        version_slug = kwargs.get('version_slug')

        if version_slug is None:
            version_slug = project.get_default_version()
        if external is None:
            external = self._is_external(project, version_slug)

        canonical_project = self._get_canonical_project(project)
        custom_domain = canonical_project.get_canonical_custom_domain()
        use_custom_domain = self._use_custom_domain(custom_domain)

        if external:
            domain = self._get_external_subdomain(canonical_project, version_slug)
        elif use_custom_domain:
            domain = custom_domain.domain
        elif self._use_subdomain():
            domain = self._get_project_subdomain(canonical_project)
        else:
            domain = settings.PRODUCTION_DOMAIN

        use_https_protocol = any([
            # Rely on the ``Domain.https`` field
            use_custom_domain and custom_domain.https,
            # or force it if specified
            require_https,
            # or fallback to settings
            settings.PUBLIC_DOMAIN_USES_HTTPS and
            settings.PUBLIC_DOMAIN and
            any([
                settings.PUBLIC_DOMAIN in domain,
                settings.RTD_EXTERNAL_VERSION_DOMAIN in domain,
            ]),
        ])
        protocol = 'https' if use_https_protocol else 'http'

        path = self.resolve_path(
            project, filename=filename, **kwargs
        )
        return urlunparse((protocol, domain, path, '', query_params, ''))

    def _get_canonical_project_data(self, project):
        """
        Returns a tuple with (project, subproject_slug) from the canonical project of `project`.

        We currently support more than 2 levels of nesting subprojects and translations,
        but we only serve 2 levels to avoid sticking in the loop.
        This means, we can have the following cases:

        - The project isn't a translation or subproject

          We serve the documentation from the domain of the project itself
          (main.docs.com/).

        - The project is a translation of a project

          We serve the documentation from the domain of the main translation
          (main.docs.com/es/).

        - The project is a subproject of a project

          We serve the documentation from the domain of the super project
          (main.docs.com/projects/subproject/).

        - The project is a translation, and the main translation is a subproject of a project, like:

          - docs
          - api (subproject of ``docs``)
          - api-es (translation of ``api``, and current project to be served)

          We serve the documentation from the domain of the super project
          (docs.docs.com/projects/api/es/).

        - The project is a subproject, and the superproject is a translation of a project, like:

          - docs
          - docs-es (translation of ``docs``)
          - api-es (subproject of ``docs-es``, and current project to be served)

          We serve the documentation from the domain of the super project (the translation),
          this is docs-es.docs.com/projects/api-es/es/.
          We aren't going to support this case for now.

        In summary: If the project is a subproject,
        we don't care if the superproject is a translation,
        we always serve from the domain of the superproject.
        If the project is a translation,
        we need to check if the main translation is a subproject.
        """
        main_project = project
        subproject_slug = None

        main_language_project = main_project.main_language_project
        if main_language_project:
            main_project = main_language_project

        relation = main_project.get_parent_relationship()
        if relation:
            main_project = relation.parent
            subproject_slug = relation.alias

        return (main_project, subproject_slug)

    def _get_canonical_project(self, project, projects=None):
        """
        Recursively get canonical project for subproject or translations.

        We need to recursively search here as a nested translations inside
        subprojects, and vice versa, are supported.

        :type project: Project
        :type projects: List of projects for iteration
        :rtype: Project
        """
        # Track what projects have already been traversed to avoid infinite
        # recursion. We can't determine a root project well here, so you get
        # what you get if you have configured your project in a strange manner
        if projects is None:
            projects = {project}
        else:
            projects.add(project)

        next_project = None
        if project.main_language_project:
            next_project = project.main_language_project
        else:
            relation = project.get_parent_relationship()
            if relation:
                next_project = relation.parent

        if next_project and next_project not in projects:
            return self._get_canonical_project(next_project, projects)
        return project

    def _get_external_subdomain(self, project, version_slug):
        """Determine domain for an external version."""
        subdomain_slug = project.slug.replace('_', '-')
        # Version slug is in the domain so we can properly serve single-version projects
        # and have them resolve the proper version from the PR.
        return f'{subdomain_slug}--{version_slug}.{settings.RTD_EXTERNAL_VERSION_DOMAIN}'

    def _get_project_subdomain(self, project):
        """Determine canonical project domain as subdomain."""
        subdomain_slug = project.slug.replace('_', '-')
        return '{}.{}'.format(subdomain_slug, settings.PUBLIC_DOMAIN)

    def _is_external(self, project, version_slug):
        type_ = (
            project.versions
            .values_list('type', flat=True)
            .filter(slug=version_slug)
            .first()
        )
        return type_ == EXTERNAL

    def _fix_filename(self, project, filename):
        """
        Force filenames that might be HTML file paths into proper URL's.

        This basically means stripping /.
        """
        filename = filename.lstrip('/')
        return filename

    def _use_custom_domain(self, custom_domain):
        """
        Make decision about whether to use a custom domain to serve docs.

        Always use the custom domain if it exists.

        :param custom_domain: Domain instance or ``None``
        :type custom_domain: readthedocs.projects.models.Domain
        """
        return custom_domain is not None

    def _use_subdomain(self):
        """Make decision about whether to use a subdomain to serve docs."""
        return settings.USE_SUBDOMAIN and settings.PUBLIC_DOMAIN is not None


class Resolver(SettingsOverrideObject):

    _default_class = ResolverBase
    _override_setting = 'RESOLVER_CLASS'


resolver = Resolver()
resolve_path = resolver.resolve_path
resolve_domain = resolver.resolve_domain
resolve = resolver.resolve
