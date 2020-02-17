"""URL resolver for documentation."""

import logging
from urllib.parse import urlunparse

from django.conf import settings

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.constants import PRIVATE
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
            private=False,
            single_version=None,
            subproject_slug=None,
            subdomain=None,
            cname=None,
    ):
        """Resolve a with nothing smart, just filling in the blanks."""
        # Only support `/docs/project' URLs outside our normal environment. Normally
        # the path should always have a subdomain or CNAME domain
        # pylint: disable=unused-argument
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
            private=None,
    ):
        """Resolve a URL with a subset of fields defined."""
        cname = cname or project.get_canonical_custom_domain()
        version_slug = version_slug or project.get_default_version()
        language = language or project.language

        if private is None:
            private, _ = self._get_private_and_external(project, version_slug)

        filename = self._fix_filename(project, filename)

        current_project = project
        project_slug = project.slug
        subproject_slug = None
        # We currently support more than 2 levels of nesting subprojects and
        # translations, only loop twice to avoid sticking in the loop
        for _ in range(0, 2):
            main_language_project = current_project.main_language_project
            relation = current_project.get_parent_relationship()

            if main_language_project:
                current_project = main_language_project
                project_slug = main_language_project.slug
                language = project.language
                subproject_slug = None
            elif relation:
                current_project = relation.parent
                project_slug = relation.parent.slug
                subproject_slug = relation.alias
                cname = relation.parent.domains.filter(canonical=True).first()
            else:
                break

        single_version = bool(project.single_version or single_version)

        return self.base_resolve_path(
            project_slug=project_slug,
            filename=filename,
            version_slug=version_slug,
            language=language,
            single_version=single_version,
            subproject_slug=subproject_slug,
            cname=cname,
            private=private,
            subdomain=subdomain,
        )

    def resolve_domain(self, project, private=None):
        # pylint: disable=unused-argument
        canonical_project = self._get_canonical_project(project)
        domain = canonical_project.get_canonical_custom_domain()
        if domain:
            return domain.domain

        if self._use_subdomain():
            return self._get_project_subdomain(canonical_project)

        return settings.PRODUCTION_DOMAIN

    def resolve(
            self, project, require_https=False, filename='', query_params='',
            private=None, external=None, **kwargs
    ):
        version_slug = kwargs.get('version_slug')

        if private is None or external is None:
            if version_slug is None:
                version_slug = project.get_default_version()
            private, external = self._get_private_and_external(project, version_slug)

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
            settings.PUBLIC_DOMAIN in domain,
        ])
        protocol = 'https' if use_https_protocol else 'http'

        path = self.resolve_path(
            project, filename=filename, private=private, **kwargs
        )
        return urlunparse((protocol, domain, path, '', query_params, ''))

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
            projects = [project]
        else:
            projects.append(project)

        next_project = None
        relation = project.get_parent_relationship()
        if project.main_language_project:
            next_project = project.main_language_project
        elif relation:
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

    def _get_private_and_external(self, project, version_slug):
        from readthedocs.builds.models import Version
        try:
            version = project.versions.get(slug=version_slug)
            private = version.privacy_level == PRIVATE
            external = version.type == EXTERNAL
        except Version.DoesNotExist:
            private = settings.DEFAULT_PRIVACY_LEVEL == PRIVATE
            external = False
        return private, external

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
        return True if custom_domain is not None else False

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
