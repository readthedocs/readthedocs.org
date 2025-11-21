"""URL resolver for documentation."""

from functools import cache
from urllib.parse import urlunparse

import structlog
from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.core.utils.url import unsafe_join_url_path
from readthedocs.projects.constants import MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import get_feature


log = structlog.get_logger(__name__)


class Resolver:
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

    .. note::

       Several methods ara cached per each instance of the resolver
       to avoid hitting the database multiple times for the same project.

       A global instance of the resolver shouldn't be used,
       as resources can change, and results from the resolver will be out of date.
       Instead, a shared instance of the resolver should be used
       when doing multiple resolutions for the same set of projects/versions.
    """

    def base_resolve_path(
        self,
        filename,
        version_slug=None,
        language=None,
        versioning_scheme=None,
        project_relationship=None,
        custom_prefix=None,
    ):
        """
        Build a path using the given fields.

        For example, if custom prefix is given, the path will be prefixed with it.
        In case of a subproject (project_relationship is given),
        the path will be prefixed with the subproject prefix
        (defaults to ``/projects/<subproject-slug>/``).

        Then we add the filename, version_slug and language to the path
        depending on the versioning scheme.
        """
        path = "/"

        if project_relationship:
            path = unsafe_join_url_path(path, project_relationship.subproject_prefix)

        # If the project has a custom prefix, we use it.
        if custom_prefix:
            path = unsafe_join_url_path(path, custom_prefix)

        if versioning_scheme == SINGLE_VERSION_WITHOUT_TRANSLATIONS:
            path = unsafe_join_url_path(path, filename)
        elif versioning_scheme == MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS:
            path = unsafe_join_url_path(path, f"{version_slug}/{filename}")
        else:
            path = unsafe_join_url_path(path, f"{language}/{version_slug}/{filename}")

        return path

    def resolve_path(
        self,
        project,
        filename="",
        version_slug=None,
        language=None,
    ):
        """Resolve a URL with a subset of fields defined."""
        version_slug = version_slug or project.get_default_version()
        language = language or project.language

        filename = self._fix_filename(filename)

        parent_project, project_relationship = self._get_canonical_project(project)

        # If the project is a subproject, we use the custom prefix and versioning scheme
        # of the child of the relationship, this is since the project
        # could be a translation. For a project that isn't a subproject,
        # we use the custom prefix and versioning scheme of the parent project.
        if project_relationship:
            custom_prefix = project_relationship.child.custom_prefix
            versioning_scheme = project_relationship.child.versioning_scheme
        else:
            custom_prefix = parent_project.custom_prefix
            versioning_scheme = parent_project.versioning_scheme

        return self.base_resolve_path(
            filename=filename,
            version_slug=version_slug,
            language=language,
            versioning_scheme=versioning_scheme,
            project_relationship=project_relationship,
            custom_prefix=custom_prefix,
        )

    def resolve_version(self, project, version=None, filename="/"):
        """
        Get the URL for a specific version of a project.

        If no version is given, the default version is used.

        Use this instead of ``resolve`` if you have the version object already.
        """
        if not version:
            default_version_slug = project.get_default_version()
            version = project.versions(manager=INTERNAL).get(slug=default_version_slug)

        domain, use_https = self._get_project_domain(
            project,
            external_version_slug=version.slug if version.is_external else None,
        )
        path = self.resolve_path(
            project=project,
            filename=filename,
            version_slug=version.slug,
            language=project.language,
        )
        protocol = "https" if use_https else "http"
        return urlunparse((protocol, domain, path, "", "", ""))

    def resolve_project(self, project, filename="/"):
        """
        Get the URL for a project.

        This is the URL where the project is served from,
        it doesn't include the version or language.

        Useful to link to a known filename in the project.
        """
        domain, use_https = self._get_project_domain(project)
        protocol = "https" if use_https else "http"
        return urlunparse((protocol, domain, filename, "", "", ""))

    @cache
    def _get_project_domain(self, project, external_version_slug=None, use_canonical_domain=True):
        """
        Get the domain from where the documentation of ``project`` is served from.

        :param project: Project object
        :param bool use_canonical_domain: If `True` use its canonical custom domain if available.
        :returns: Tuple of ``(domain, use_https)``.

        Note that we are using ``cache`` decorator on this function.
        This is useful when generating the flyout addons response since we call
        ``resolver.resolve`` multi times for the same ``Project``.
        This cache avoids hitting the DB to get the canonical custom domain over and over again.
        """
        use_https = settings.PUBLIC_DOMAIN_USES_HTTPS
        canonical_project, _ = self._get_canonical_project(project)
        domain = self._get_project_subdomain(canonical_project)
        if external_version_slug:
            domain = self._get_external_subdomain(canonical_project, external_version_slug)
        elif use_canonical_domain and self._use_cname(canonical_project):
            domain_object = canonical_project.canonical_custom_domain
            if domain_object:
                use_https = domain_object.https
                domain = domain_object.domain

        return domain, use_https

    def get_domain(self, project, use_canonical_domain=True):
        domain, use_https = self._get_project_domain(
            project, use_canonical_domain=use_canonical_domain
        )
        protocol = "https" if use_https else "http"
        return urlunparse((protocol, domain, "", "", "", ""))

    def get_domain_without_protocol(self, project, use_canonical_domain=True):
        """
        Get the domain from where the documentation of ``project`` is served from.

        This doesn't include the protocol.

        :param project: Project object
        :param bool use_canonical_domain: If `True` use its canonical custom domain if available.
        """
        domain, _ = self._get_project_domain(project, use_canonical_domain=use_canonical_domain)
        return domain

    def resolve(
        self,
        project,
        filename="",
        query_params="",
        external=None,
        **kwargs,
    ):
        """
        Resolve the URL of the project/version_slug/filename combination.

        :param project: Project to resolve.
        :param filename: exact filename the resulting URL should contain.
        :param query_params: query string params the resulting URL should contain.
        :param external: whether or not the resolved URL would be external (`*.readthedocs.build`).
        :param kwargs: extra attributes to be passed to ``resolve_path``.
        """
        version_slug = kwargs.get("version_slug")

        if version_slug is None:
            version_slug = project.get_default_version()
        if external is None:
            external = self._is_external(project, version_slug)

        domain, use_https = self._get_project_domain(
            project,
            external_version_slug=version_slug if external else None,
        )
        protocol = "https" if use_https else "http"
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
        domain, use_https = self._get_project_domain(
            project, external_version_slug=external_version_slug
        )
        protocol = "https" if use_https else "http"
        path = project.subproject_prefix
        return urlunparse((protocol, domain, path, "", "", ""))

    @cache
    def _get_canonical_project(self, project):
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

        return parent_project, relationship

    def _get_external_subdomain(self, project, version_slug):
        """Determine domain for an external version."""
        subdomain_slug = project.slug.replace("_", "-")
        # Version slug is in the domain so we can properly serve single-version projects
        # and have them resolve the proper version from the PR.
        return f"{subdomain_slug}--{version_slug}.{settings.RTD_EXTERNAL_VERSION_DOMAIN}"

    def _get_project_subdomain(self, project):
        """Determine canonical project domain as subdomain."""
        subdomain_slug = project.slug.replace("_", "-")
        return "{}.{}".format(subdomain_slug, settings.PUBLIC_DOMAIN)

    @cache
    def _is_external(self, project, version_slug):
        type_ = project.versions.values_list("type", flat=True).filter(slug=version_slug).first()
        return type_ == EXTERNAL

    def _fix_filename(self, filename):
        """
        Force filenames that might be HTML file paths into proper URL's.

        This basically means stripping /.
        """
        filename = filename.lstrip("/")
        return filename

    def _use_cname(self, project):
        """Test if to allow direct serving for project on CNAME."""
        return bool(get_feature(project, feature_type=TYPE_CNAME))
