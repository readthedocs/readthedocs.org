import structlog
from dataclasses import dataclass
from readthedocs.projects.constants import LANGUAGES
import re
from django.conf import settings
from urllib.parse import urlparse

from readthedocs.builds.models import Version

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.models import Domain, Project

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class UnresolvedURL:
    canonical_project: Project
    project: Project
    version: Version = None
    filename: str = None
    query: str = None
    fragment: str = None
    domain: Domain = None
    external: bool = False


class UnresolverBase:

    LANGUAGES_CODES = {code for code, _ in LANGUAGES}

    def unresolve(self, url, normalize_filename=True):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.

        :param url: Full URL to unresolve (including the protocol and domain part).
        :param normalize_filename: If `True` the filename will be normalized
         to end with ``/index.html``.
        """
        parsed = urlparse(url)
        domain = self.get_domain_from_host(parsed.netloc)
        project_slug, domain_object, external = self.unresolve_domain(domain)
        if not project_slug:
            return None

        canonical_project = Project.objects.filter(slug=project_slug).first()
        if not canonical_project:
            return None

        project, version, filename = self._unresolve_path(
            canonical_project=canonical_project,
            path=parsed.path,
        )

        if normalize_filename and filename and filename.endswith("/"):
            filename += "index.html"

        return UnresolvedURL(
            canonical_project=canonical_project,
            project=project or canonical_project,
            version=version,
            filename=filename,
            query=parsed.query,
            fragment=parsed.fragment,
            domain=domain_object,
            external=external,
        )

    @staticmethod
    def _normalize_filename(filename):
        """Normalize filename to always start with ``/``."""
        filename = filename or "/"
        if not filename.startswith("/"):
            filename = "/" + filename
        return filename

    def _match_multiversion_project(self, canonical_project, path):
        """
        Try to match a multiversion project.

        If the translation exists, we return a result even if the version doesn't,
        so the translation is taken as the canonical project (useful for 404 pages).
        """
        # This pattern matches:
        # - /en
        # - /en/
        # - /en/latest
        # - /en/latest/
        # - /en/latest/file/name/
        versioned_pattern = re.compile(
            r"^/(?P<language>[^/]+)(/((?P<version>[^/]+)(/(?P<file>.*))?)?)?$"
        )
        # if canonical_project.pattern:
        #    versioned_pattern = re.compile(canonical_project.pattern)

        match = versioned_pattern.match(path)
        if not match:
            return None

        language = match.group("language")
        version_slug = match.group("version")
        file = self._normalize_filename(match.group("file"))

        if language not in self.LANGUAGES_CODES:
            return None

        if canonical_project.language == language:
            project = canonical_project
        else:
            project = canonical_project.translations.filter(
                language=language
            ).first()

        if project:
            version = project.versions.filter(slug=version_slug).first()
            if version:
                return project, version, file
            return project, None, None

        return None

    def _match_subproject(self, canonical_project, path):
        """
        Try to match a subproject.

        If the subproject exists, we try to resolve the rest of the path
        with the subproject as the canonical project.
        """
        # This pattern matches:
        # - /projects/subproject
        # - /projects/subproject/
        # - /projects/subproject/file/name/
        subproject_pattern = re.compile(
            r"^/projects/(?P<project>[^/]+)(/(?P<file>.*))?$"
        )
        # if canonical_project.subproject_pattern:
        #    subproject_pattern = re.compile(canonical_project.subproject_pattern)

        match = subproject_pattern.match(path)
        if not match:
            return None

        project_slug = match.group("project")
        file = self._normalize_filename(match.group("file"))
        # TODO: check if all of our projects have an alias.
        project_relationship = (
            canonical_project.subprojects.filter(alias=project_slug)
            .prefetch_related("child")
            .first()
        )
        if project_relationship:
            return self._unresolve_path(
                canonical_project=project_relationship.child,
                path=file,
                check_subprojects=False,
            )
        return None

    def _match_single_version_project(self, canonical_project, path):
        """
        Try to match a single version project.

        With the default pattern any path will match.
        """
        # This pattern matches:
        # -
        # - /
        # - /file/name/
        single_version_pattern = re.compile(r"^(?P<file>.+)$")

        # if canonical_project.pattern:
        #     single_version_pattern = re.compile(canonical_project.pattern)

        match = single_version_pattern.match(path)
        if not match:
            return None

        file = self._normalize_filename(match.group("file"))
        version = canonical_project.versions.filter(slug=canonical_project.default_version).first()
        if version:
            return canonical_project, version, file
        return canonical_project, None, None

    def _unresolve_path(self, canonical_project, path, check_subprojects=True):
        """
        Unresolve `path` with `canonical_project` as base.

        If the returned project is `None`, then we weren't able to
        unresolve the path into a project.

        If the returned version is `None`, then we weren't able to
        unresolve the path into a valid version of the project.

        :param canonical_project: The project that owns the path.
        :param path: The path to unresolve.
        :param check_subprojects: If we should check for subprojects,
         this is used to call this function recursively.

        :returns: A tuple with: project, version, and file name.
        """
        # Multiversion project.
        if not canonical_project.single_version:
            response = self._match_multiversion_project(
                canonical_project=canonical_project,
                path=path,
            )
            if response:
                return response

        # Subprojects.
        if check_subprojects:
            response = self._match_subproject(
                canonical_project=canonical_project,
                path=path,
            )
            if response:
                return response

        # Single version project.
        if canonical_project.single_version:
            response = self._match_single_version_project(
                canonical_project=canonical_project,
                path=path,
            )
            if response:
                return response

        return None, None, None

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
        :returns: A tuple with: the project slug, domain object, and if the domain
        is from an external version.
        """
        public_domain = self.get_domain_from_host(settings.PUBLIC_DOMAIN)
        external_domain = self.get_domain_from_host(settings.RTD_EXTERNAL_VERSION_DOMAIN)

        subdomain, *rest_of_domain = domain.split(".", maxsplit=1)
        rest_of_domain = rest_of_domain[0] if rest_of_domain else ""

        if public_domain in domain:
            # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`.
            if public_domain == rest_of_domain:
                project_slug = subdomain
                return project_slug, None, False

            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example,
            # but these might be phishing, so let's ignore them for now.
            return None, None, False

        if external_domain in domain:
            # Serve custom versions on external-host-domain.
            if external_domain == rest_of_domain:
                try:
                    project_slug, _ = subdomain.rsplit("--", maxsplit=1)
                    return project_slug, None, True
                except ValueError:
                    return None, None, False

        # Custom domain.
        domain_object = (
            Domain.objects.filter(domain=domain).prefetch_related("project").first()
        )
        if domain_object:
            project_slug = domain_object.project.slug
            return project_slug, domain_object, False

        return None, None, None


class Unresolver(SettingsOverrideObject):

    _default_class = UnresolverBase


unresolver = Unresolver()
unresolve = unresolver.unresolve
