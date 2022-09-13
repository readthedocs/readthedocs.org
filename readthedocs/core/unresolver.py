import re
from dataclasses import dataclass
from urllib.parse import ParseResult, urlparse

import structlog
from django.conf import settings

from readthedocs.builds.models import Version
from readthedocs.constants import pattern_opts
from readthedocs.projects.models import Domain, Project

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class UnresolvedURL:

    """Dataclass with the parts of an unresolved URL."""

    # This is the project that owns the domain,
    # this usually is the parent project of a translation or subproject.
    parent_project: Project

    # The current project we are serving the docs from.
    # It can be the same as parent_project.
    project: Project

    version: Version = None
    filename: str = None
    parsed_url: ParseResult = None
    domain: Domain = None
    external: bool = False


class Unresolver:
    # This pattern matches:
    # - /en
    # - /en/
    # - /en/latest
    # - /en/latest/
    # - /en/latest/file/name/
    multiversion_pattern = re.compile(
        r"^/(?P<language>{lang_slug})(/((?P<version>{version_slug})(/(?P<file>{filename_slug}))?)?)?$".format(  # noqa
            **pattern_opts
        )
    )

    # This pattern matches:
    # - /projects/subproject
    # - /projects/subproject/
    # - /projects/subproject/file/name/
    subproject_pattern = re.compile(
        r"^/projects/(?P<project>{project_slug}+)(/(?P<file>{filename_slug}))?$".format(
            **pattern_opts
        )
    )

    def unresolve(self, url, add_index=True):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.

        :param url: Full URL to unresolve (including the protocol and domain part).
        :param add_index: If `True` the filename will be normalized
         to end with ``/index.html``.
        """
        parsed = urlparse(url)
        domain = self.get_domain_from_host(parsed.netloc)
        project_slug, domain_object, external_version_slug = self.unresolve_domain(
            domain
        )
        if not project_slug:
            return None

        parent_project = Project.objects.filter(slug=project_slug).first()
        if not parent_project:
            return None

        project, version, filename = self._unresolve_path(
            parent_project=parent_project,
            path=parsed.path,
        )

        # Make sure we are serving the external version from the subdomain.
        if external_version_slug and version:
            if external_version_slug != version.slug:
                log.warning(
                    "Invalid version for external domain.",
                    domain=domain,
                    version_slug=version.slug,
                )
                version = None
                filename = None
            elif not version.is_external:
                log.warning(
                    "Attempt of serving a non-external version from RTD_EXTERNAL_VERSION_DOMAIN.",
                    domain=domain,
                    version_slug=version.slug,
                    version_type=version.type,
                    url=url,
                )
                version = None
                filename = None

        if add_index and filename and filename.endswith("/"):
            filename += "index.html"

        return UnresolvedURL(
            parent_project=parent_project,
            project=project or parent_project,
            version=version,
            filename=filename,
            parsed_url=parsed,
            domain=domain_object,
            external=bool(external_version_slug),
        )

    @staticmethod
    def _normalize_filename(filename):
        """Normalize filename to always start with ``/``."""
        filename = filename or "/"
        if not filename.startswith("/"):
            filename = "/" + filename
        return filename

    def _match_multiversion_project(self, parent_project, path):
        """
        Try to match a multiversion project.

        If the translation exists, we return a result even if the version doesn't,
        so the translation is taken as the current project (useful for 404 pages).
        """
        match = self.multiversion_pattern.match(path)
        if not match:
            return None

        language = match.group("language")
        version_slug = match.group("version")
        file = self._normalize_filename(match.group("file"))

        if parent_project.language == language:
            project = parent_project
        else:
            project = parent_project.translations.filter(language=language).first()

        if project:
            version = project.versions.filter(slug=version_slug).first()
            if version:
                return project, version, file
            return project, None, None

        return None

    def _match_subproject(self, parent_project, path):
        """
        Try to match a subproject.

        If the subproject exists, we try to resolve the rest of the path
        with the subproject as the canonical project.

        If the subproject exists, we return a result even if version doesn't,
        so the subproject is taken as the current project (useful for 404 pages).
        """
        match = self.subproject_pattern.match(path)
        if not match:
            return None

        project_slug = match.group("project")
        file = self._normalize_filename(match.group("file"))
        project_relationship = (
            parent_project.subprojects.filter(alias=project_slug)
            .prefetch_related("child")
            .first()
        )
        if project_relationship:
            # We use the subproject as the new parent project
            # to resolve the rest of the path relative to it.
            subproject = project_relationship.child
            response = self._unresolve_path(
                parent_project=subproject,
                path=file,
                check_subprojects=False,
            )
            # If we got a valid response, return that,
            # otherwise return the current subproject
            # as the current project without a valid version or path.
            if response:
                return response
            return subproject, None, None
        return None

    def _match_single_version_project(self, parent_project, path):
        """
        Try to match a single version project.

        By default any path will match.
        """
        file = self._normalize_filename(path)
        version = parent_project.versions.filter(
            slug=parent_project.default_version
        ).first()
        if version:
            return parent_project, version, file
        return parent_project, None, None

    def _unresolve_path(self, parent_project, path, check_subprojects=True):
        """
        Unresolve `path` with `parent_project` as base.

        If the returned project is `None`, then we weren't able to
        unresolve the path into a project.

        If the returned version is `None`, then we weren't able to
        unresolve the path into a valid version of the project.

        :param parent_project: The project that owns the path.
        :param path: The path to unresolve.
        :param check_subprojects: If we should check for subprojects,
         this is used to call this function recursively.

        :returns: A tuple with: project, version, and file name.
        """
        # Multiversion project.
        if not parent_project.single_version:
            response = self._match_multiversion_project(
                parent_project=parent_project,
                path=path,
            )
            if response:
                return response

        # Subprojects.
        if check_subprojects:
            response = self._match_subproject(
                parent_project=parent_project,
                path=path,
            )
            if response:
                return response

        # Single version project.
        if parent_project.single_version:
            response = self._match_single_version_project(
                parent_project=parent_project,
                path=path,
            )
            if response:
                return response

        return parent_project, None, None

    @staticmethod
    def get_domain_from_host(host):
        """
        Get the normalized domain from a hostname.

        A hostname can include the port.
        """
        return host.lower().split(":")[0]

    # TODO: make this a private method once
    # proxito uses the unresolve method directly.
    def unresolve_domain(self, domain):
        """
        Unresolve domain by extracting relevant information from it.

        :param str domain: Domain to extract the information from.
        :returns: A tuple with: the project slug, domain object, and the
         external version slug if the domain is from an external version.
        """
        public_domain = self.get_domain_from_host(settings.PUBLIC_DOMAIN)
        external_domain = self.get_domain_from_host(
            settings.RTD_EXTERNAL_VERSION_DOMAIN
        )

        subdomain, *root_domain = domain.split(".", maxsplit=1)
        root_domain = root_domain[0] if root_domain else ""

        if public_domain in domain:
            # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`.
            if public_domain == root_domain:
                project_slug = subdomain
                log.debug("Public domain.", domain=domain)
                return project_slug, None, None

            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com)
            # for example, but these might be phishing, so let's ignore them for now.
            log.warning("Weird variation of our domain.", domain=domain)
            return None, None, None

        # Serve PR builds on external_domain host.
        if external_domain == root_domain:
            try:
                project_slug, version_slug = subdomain.rsplit("--", maxsplit=1)
                log.debug("External versions domain.", domain=domain)
                return project_slug, None, version_slug
            except ValueError:
                log.info("Invalid format of external versions domain.", domain=domain)
                return None, None, None

        # Custom domain.
        domain_object = (
            Domain.objects.filter(domain=domain).prefetch_related("project").first()
        )
        if domain_object:
            log.debug("Custom domain.", domain=domain)
            project_slug = domain_object.project.slug
            return project_slug, domain_object, False

        log.info("Invalid domain.", domain=domain)
        return None, None, None


unresolver = Unresolver()
unresolve = unresolver.unresolve
