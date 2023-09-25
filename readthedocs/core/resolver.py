"""URL resolver for documentation."""
from urllib.parse import urlunparse

import structlog
from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.core.utils.url import unsafe_join_url_path
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import get_feature

log = structlog.get_logger(__name__)


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
        project_relationship=None,
        subdomain=None,
        cname=None,
        custom_prefix=None,
    ):
        """
        Build a path using the given fields.

        We first build a format string based on the given fields,
        then we just call ``string.format()`` with the given values.

        For example, if custom prefix is given, the path will be prefixed with it.
        In case of a subproject (project_relationship is given),
        the path will be prefixed with the subproject prefix
        (defaults to ``/projects/<subproject-slug>/``).
        """
        # Only support `/docs/project' URLs outside our normal environment. Normally
        # the path should always have a subdomain or CNAME domain
        if subdomain or cname or self._use_subdomain():
            path = "/"
        else:
            path = "/docs/{project}/"

        if project_relationship:
            path = unsafe_join_url_path(path, project_relationship.subproject_prefix)

        # If the project has a custom prefix, we use it.
        if custom_prefix:
            path = unsafe_join_url_path(path, custom_prefix)

        if single_version:
            path = unsafe_join_url_path(path, "{filename}")
        else:
            path = unsafe_join_url_path(path, "{language}/{version}/{filename}")

        subproject_alias = project_relationship.alias if project_relationship else ""
        return path.format(
            project=project_slug,
            filename=filename,
            version=version_slug,
            language=language,
            subproject=subproject_alias,
        )

    def resolve_path(
        self,
        project,
        filename="",
        version_slug=None,
        language=None,
        single_version=None,
        subdomain=None,
        cname=None,
    ):
        """Resolve a URL with a subset of fields defined."""
        version_slug = version_slug or project.get_default_version()
        language = language or project.language

        filename = self._fix_filename(filename)

        parent_project, project_relationship = self._get_canonical_project_data(project)
        cname = (
            cname
            or self._use_subdomain()
            or parent_project.get_canonical_custom_domain()
        )
        single_version = bool(project.single_version or single_version)

        # If the project is a subproject, we use the custom prefix
        # of the child of the relationship, this is since the project
        # could be a translation. For a project that isn't a subproject,
        # we use the custom prefix of the parent project.
        if project_relationship:
            custom_prefix = project_relationship.child.custom_prefix
        else:
            custom_prefix = parent_project.custom_prefix

        return self.base_resolve_path(
            project_slug=parent_project.slug,
            filename=filename,
            version_slug=version_slug,
            language=language,
            single_version=single_version,
            project_relationship=project_relationship,
            cname=cname,
            subdomain=subdomain,
            custom_prefix=custom_prefix,
        )

    def resolve_domain(self, project, use_canonical_domain=True):
        """
        Get the domain from where the documentation of ``project`` is served from.

        :param project: Project object
        :param bool use_canonical_domain: If `True` use its canonical custom domain if available.
        """
        canonical_project = self._get_canonical_project(project)
        if use_canonical_domain and self._use_cname(canonical_project):
            domain = canonical_project.get_canonical_custom_domain()
            if domain:
                return domain.domain

        if self._use_subdomain():
            return self._get_project_subdomain(canonical_project)

        return settings.PRODUCTION_DOMAIN

    def resolve(
        self,
        project,
        require_https=False,
        filename="",
        query_params="",
        external=None,
        **kwargs,
    ):
        version_slug = kwargs.get("version_slug")

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

        use_https_protocol = any(
            [
                # Rely on the ``Domain.https`` field
                use_custom_domain and custom_domain.https,
                # or force it if specified
                require_https,
                # or fallback to settings
                settings.PUBLIC_DOMAIN_USES_HTTPS
                and settings.PUBLIC_DOMAIN
                and any(
                    [
                        settings.PUBLIC_DOMAIN in domain,
                        settings.RTD_EXTERNAL_VERSION_DOMAIN in domain,
                    ]
                ),
            ]
        )
        protocol = "https" if use_https_protocol else "http"

        path = self.resolve_path(project, filename=filename, **kwargs)
        return urlunparse((protocol, domain, path, "", query_params, ""))

    def get_subproject_url_prefix(self, project, external_version_slug=None):
        """
        Get the URL prefix from where the documentation of a subproject is served from.

        This doesn't include the version or language. For example:

        - https://docs.example.com/projects/<project-slug>/

        This will respect the custom subproject prefix if it's defined.

        :param project: Project object to get the root URL from
        :param external_version_slug: If given, resolve using the external version domain.
        """
        canonical_project = self._get_canonical_project(project)
        use_custom_domain = self._use_cname(canonical_project)
        custom_domain = canonical_project.get_canonical_custom_domain()
        if external_version_slug:
            domain = self._get_external_subdomain(
                canonical_project, external_version_slug
            )
            use_https = settings.PUBLIC_DOMAIN_USES_HTTPS
        elif use_custom_domain and custom_domain:
            domain = custom_domain.domain
            use_https = custom_domain.https
        else:
            domain = self._get_project_subdomain(canonical_project)
            use_https = settings.PUBLIC_DOMAIN_USES_HTTPS

        protocol = "https" if use_https else "http"
        path = project.subproject_prefix
        return urlunparse((protocol, domain, path, "", "", ""))

    def _get_canonical_project_data(self, project):
        """
        Get the parent project and subproject relationship from the canonical project of `project`.

        We don't support more than 2 levels of nesting subprojects and translations,
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
        parent_project = project

        main_language_project = parent_project.main_language_project
        if main_language_project:
            parent_project = main_language_project

        relationship = parent_project.parent_relationship
        if relationship:
            parent_project = relationship.parent

        return (parent_project, relationship)

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
            relation = project.parent_relationship
            if relation:
                next_project = relation.parent

        if next_project and next_project not in projects:
            return self._get_canonical_project(next_project, projects)
        return project

    def _get_external_subdomain(self, project, version_slug):
        """Determine domain for an external version."""
        subdomain_slug = project.slug.replace("_", "-")
        # Version slug is in the domain so we can properly serve single-version projects
        # and have them resolve the proper version from the PR.
        return (
            f"{subdomain_slug}--{version_slug}.{settings.RTD_EXTERNAL_VERSION_DOMAIN}"
        )

    def _get_project_subdomain(self, project):
        """Determine canonical project domain as subdomain."""
        subdomain_slug = project.slug.replace("_", "-")
        return "{}.{}".format(subdomain_slug, settings.PUBLIC_DOMAIN)

    def _is_external(self, project, version_slug):
        type_ = (
            project.versions.values_list("type", flat=True)
            .filter(slug=version_slug)
            .first()
        )
        return type_ == EXTERNAL

    def _fix_filename(self, filename):
        """
        Force filenames that might be HTML file paths into proper URL's.

        This basically means stripping /.
        """
        filename = filename.lstrip("/")
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

    def _use_cname(self, project):
        """Test if to allow direct serving for project on CNAME."""
        return bool(get_feature(project, feature_type=TYPE_CNAME))


class Resolver(SettingsOverrideObject):
    _default_class = ResolverBase
    _override_setting = "RESOLVER_CLASS"


resolver = Resolver()
resolve_path = resolver.resolve_path
resolve_domain = resolver.resolve_domain
resolve = resolver.resolve
