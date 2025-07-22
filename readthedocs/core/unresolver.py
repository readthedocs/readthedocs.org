import re
from dataclasses import dataclass
from enum import Enum
from enum import auto
from urllib.parse import ParseResult
from urllib.parse import urlparse

import structlog
from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.models import Version
from readthedocs.constants import pattern_opts
from readthedocs.projects.constants import MULTIPLE_VERSIONS_WITH_TRANSLATIONS
from readthedocs.projects.constants import MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Domain
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


class UnresolverError(Exception):
    pass


class InvalidSchemeError(UnresolverError):
    def __init__(self, scheme):
        self.scheme = scheme


class InvalidXRTDSlugHeaderError(UnresolverError):
    pass


class DomainError(UnresolverError):
    def __init__(self, domain):
        self.domain = domain


class SuspiciousHostnameError(DomainError):
    pass


class InvalidSubdomainError(DomainError):
    pass


class InvalidExternalDomainError(DomainError):
    pass


class InvalidCustomDomainError(DomainError):
    pass


class VersionNotFoundError(UnresolverError):
    def __init__(self, project, version_slug, filename):
        self.project = project
        self.version_slug = version_slug
        self.filename = filename


class TranslationNotFoundError(UnresolverError):
    def __init__(self, project, language, version_slug, filename):
        self.project = project
        self.language = language
        self.filename = filename
        # The version doesn't exist, so we just have the slug.
        self.version_slug = version_slug


class TranslationWithoutVersionError(UnresolverError):
    def __init__(self, project, language):
        self.project = project
        self.language = language


class InvalidPathForVersionedProjectError(UnresolverError):
    def __init__(self, project, path):
        self.project = project
        self.path = path


class InvalidExternalVersionError(UnresolverError):
    def __init__(self, project, version_slug, external_version_slug):
        self.project = project
        self.version_slug = version_slug
        self.external_version_slug = external_version_slug


@dataclass(slots=True)
class UnresolvedURL:
    """Dataclass with the parts of an unresolved URL."""

    # This is the project that owns the domain,
    # this usually is the parent project of a translation or subproject.
    parent_project: Project

    # The current project we are serving the docs from.
    # It can be the same as parent_project.
    project: Project

    version: Version
    filename: str
    parsed_url: ParseResult
    domain: Domain = None
    external: bool = False


class DomainSourceType(Enum):
    """Where the custom domain was resolved from."""

    custom_domain = auto()
    public_domain = auto()
    external_domain = auto()
    http_header = auto()


@dataclass(slots=True)
class UnresolvedDomain:
    # The domain that was used to extract the information from.
    source_domain: str
    source: DomainSourceType
    project: Project
    # Domain object for custom domains.
    domain: Domain = None
    external_version_slug: str = None

    @property
    def is_from_custom_domain(self):
        return self.source == DomainSourceType.custom_domain

    @property
    def is_from_public_domain(self):
        return self.source == DomainSourceType.public_domain

    @property
    def is_from_http_header(self):
        return self.source == DomainSourceType.http_header

    @property
    def is_from_external_domain(self):
        return self.source == DomainSourceType.external_domain


def _expand_regex(pattern):
    """
    Expand a pattern with the patterns from pattern_opts.

    This is used to avoid having a long regex.
    """
    return re.compile(
        pattern.format(
            language=f"(?P<language>{pattern_opts['lang_slug']})",
            version=f"(?P<version>{pattern_opts['version_slug']})",
            filename=f"(?P<filename>{pattern_opts['filename_slug']})",
            subproject=f"(?P<subproject>{pattern_opts['project_slug']})",
        )
    )


class Unresolver:
    # This pattern matches:
    # - /en
    # - /en/
    # - /en/latest
    # - /en/latest/
    # - /en/latest/file/name/
    multiple_versions_with_translations_pattern = _expand_regex(
        # The path must have a language slug,
        # optionally a version slug followed by a filename.
        "^/{language}(/({version}(/{filename})?)?)?$"
    )

    # This pattern matches:
    # - /latest
    # - /latest/
    # - /latest/file/name/
    multiple_versions_without_translations_pattern = _expand_regex(
        # The path must have a version slug,
        # optionally followed by a filename.
        "^/{version}(/{filename})?$"
    )

    # This pattern matches:
    # - /projects/subproject
    # - /projects/subproject/
    # - /projects/subproject/file/name/
    subproject_pattern = _expand_regex(
        # The path must have the `project` alias,
        # optionally a filename, which will be recursively resolved.
        "^/{subproject}(/{filename})?$"
    )

    def unresolve_url(self, url, append_indexhtml=True):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.

        :param url: Full URL to unresolve (including the protocol and domain part).
        :param append_indexhtml: If `True` directories will be normalized
         to end with ``/index.html``.
        """
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ["http", "https"]:
            raise InvalidSchemeError(parsed_url.scheme)
        domain = parsed_url.hostname
        unresolved_domain = self.unresolve_domain(domain)
        return self._unresolve(
            unresolved_domain=unresolved_domain,
            parsed_url=parsed_url,
            append_indexhtml=append_indexhtml,
        )

    def unresolve_path(self, unresolved_domain, path, append_indexhtml=True):
        """
        Unresolve a path given a unresolved domain.

        This is the same as the unresolve method,
        but this method takes an unresolved domain
        from unresolve_domain as input.

        :param unresolved_domain: An UnresolvedDomain object.
        :param path: Path to unresolve (this shouldn't include the protocol or querystrings).
        :param append_indexhtml: If `True` directories will be normalized
         to end with ``/index.html``.
        """
        # Make sure we always have a leading slash.
        path = self._normalize_filename(path)
        # We don't call unparse() on the path,
        # since it could be parsed as a full URL if it starts with a protocol.
        parsed_url = ParseResult(scheme="", netloc="", path=path, params="", query="", fragment="")
        return self._unresolve(
            unresolved_domain=unresolved_domain,
            parsed_url=parsed_url,
            append_indexhtml=append_indexhtml,
        )

    def _unresolve(self, unresolved_domain, parsed_url, append_indexhtml):
        """
        The actual unresolver.

        Extracted into a separate method so it can be re-used by
        the unresolve and unresolve_path methods.
        """
        current_project, version, filename = self._unresolve_path_with_parent_project(
            parent_project=unresolved_domain.project,
            path=parsed_url.path,
            external_version_slug=unresolved_domain.external_version_slug,
        )

        if append_indexhtml and filename.endswith("/"):
            filename += "index.html"

        return UnresolvedURL(
            parent_project=unresolved_domain.project,
            project=current_project,
            version=version,
            filename=filename,
            parsed_url=parsed_url,
            domain=unresolved_domain.domain,
            external=unresolved_domain.is_from_external_domain,
        )

    @staticmethod
    def _normalize_filename(filename):
        """Normalize filename to always start with ``/``."""
        filename = filename or "/"
        if not filename.startswith("/"):
            filename = "/" + filename
        return filename

    def _match_multiple_versions_with_translations_project(
        self, parent_project, path, external_version_slug=None
    ):
        """
        Try to match a multiversion project.

        An exception is raised if we weren't able to find a matching version or language,
        this exception has the current project (useful for 404 pages).

        :returns: A tuple with the current project, version and filename.
         Returns `None` if there isn't a total or partial match.
        """
        custom_prefix = parent_project.custom_prefix
        if custom_prefix:
            if not path.startswith(custom_prefix):
                return None
            # pep8 and black don't agree on having a space before :,
            # so syntax is black with noqa for pep8.
            path = self._normalize_filename(path[len(custom_prefix) :])  # noqa

        match = self.multiple_versions_with_translations_pattern.match(path)
        if not match:
            return None

        language = match.group("language")
        # Normalize old language codes to lowercase with dashes.
        language = language.lower().replace("_", "-")

        version_slug = match.group("version")
        filename = self._normalize_filename(match.group("filename"))

        if parent_project.language == language:
            project = parent_project
        else:
            project = parent_project.translations.filter(language=language).first()
            if not project:
                raise TranslationNotFoundError(
                    project=parent_project,
                    language=language,
                    version_slug=version_slug,
                    filename=filename,
                )

        # If only the language part was given,
        # we can't resolve the version.
        if version_slug is None:
            raise TranslationWithoutVersionError(
                project=project,
                language=language,
            )

        if external_version_slug and external_version_slug != version_slug:
            raise InvalidExternalVersionError(
                project=project,
                version_slug=version_slug,
                external_version_slug=external_version_slug,
            )

        manager = EXTERNAL if external_version_slug else INTERNAL
        version = project.versions(manager=manager).filter(slug=version_slug).first()
        if not version:
            raise VersionNotFoundError(
                project=project, version_slug=version_slug, filename=filename
            )

        return project, version, filename

    def _match_multiple_versions_without_translations_project(
        self, parent_project, path, external_version_slug=None
    ):
        custom_prefix = parent_project.custom_prefix
        if custom_prefix:
            if not path.startswith(custom_prefix):
                return None
            # pep8 and black don't agree on having a space before :,
            # so syntax is black with noqa for pep8.
            path = self._normalize_filename(path[len(custom_prefix) :])  # noqa

        match = self.multiple_versions_without_translations_pattern.match(path)
        if not match:
            return None

        version_slug = match.group("version")
        filename = self._normalize_filename(match.group("filename"))
        project = parent_project

        if external_version_slug and external_version_slug != version_slug:
            raise InvalidExternalVersionError(
                project=project,
                version_slug=version_slug,
                external_version_slug=external_version_slug,
            )

        manager = EXTERNAL if external_version_slug else INTERNAL
        version = project.versions(manager=manager).filter(slug=version_slug).first()
        if not version:
            raise VersionNotFoundError(
                project=project, version_slug=version_slug, filename=filename
            )

        return project, version, filename

    def _match_subproject(self, parent_project, path, external_version_slug=None):
        """
        Try to match a subproject.

        If the subproject exists, we try to resolve the rest of the path
        with the subproject as the canonical project.

        :returns: A tuple with the current project, version and filename.
         Returns `None` if there isn't a total or partial match.
        """
        custom_prefix = parent_project.custom_subproject_prefix or "/projects/"
        if not path.startswith(custom_prefix):
            return None
        # pep8 and black don't agree on having a space before :,
        # so syntax is black with noqa for pep8.
        path = self._normalize_filename(path[len(custom_prefix) :])  # noqa

        match = self.subproject_pattern.match(path)
        if not match:
            return None

        subproject_alias = match.group("subproject")
        filename = self._normalize_filename(match.group("filename"))
        project_relationship = (
            parent_project.subprojects.filter(alias=subproject_alias)
            .select_related("child")
            .first()
        )
        if project_relationship:
            # We use the subproject as the new parent project
            # to resolve the rest of the path relative to it.
            subproject = project_relationship.child
            response = self._unresolve_path_with_parent_project(
                parent_project=subproject,
                path=filename,
                check_subprojects=False,
                external_version_slug=external_version_slug,
            )
            return response
        return None

    def _match_single_version_without_translations_project(
        self, parent_project, path, external_version_slug=None
    ):
        """
        Try to match a single version project.

        By default any path will match. If `external_version_slug` is given,
        that version is used instead of the project's default version.

        An exception is raised if we weren't able to find a matching version,
        this exception has the current project (useful for 404 pages).

        :returns: A tuple with the current project, version and filename.
         Returns `None` if there isn't a total or partial match.
        """
        custom_prefix = parent_project.custom_prefix
        if custom_prefix:
            if not path.startswith(custom_prefix):
                return None
            # pep8 and black don't agree on having a space before :,
            # so syntax is black with noqa for pep8.
            path = path[len(custom_prefix) :]  # noqa

        # In single version projects, any path is allowed,
        # so we don't need a regex for that.
        filename = self._normalize_filename(path)

        if external_version_slug:
            version_slug = external_version_slug
            manager = EXTERNAL
        else:
            version_slug = parent_project.default_version
            manager = INTERNAL

        version = parent_project.versions(manager=manager).filter(slug=version_slug).first()
        if not version:
            raise VersionNotFoundError(
                project=parent_project, version_slug=version_slug, filename=filename
            )

        return parent_project, version, filename

    def _unresolve_path_with_parent_project(
        self, parent_project, path, check_subprojects=True, external_version_slug=None
    ):
        """
        Unresolve `path` with `parent_project` as base.

        The returned project, version, and filename are guaranteed to not be
        `None`. An exception is raised if we weren't able to resolve the
        project, version or path/filename.

        The checks are done in the following order:

        - Check for multiple versions if the parent project
          isn't a single version project.
        - Check for subprojects.
        - Check for single versions if the parent project isn't
          a multi version project.

        :param parent_project: The project that owns the path.
        :param path: The path to unresolve.
        :param check_subprojects: If we should check for subprojects,
         this is used to call this function recursively when
         resolving the path from a subproject (we don't support subprojects of subprojects).
        :param external_version_slug: Slug of the external version.
         Used instead of the default version for single version projects
         being served under an external domain.

        :returns: A tuple with: project, version, and filename.
        """
        # Multiversion project.
        if parent_project.versioning_scheme == MULTIPLE_VERSIONS_WITH_TRANSLATIONS:
            response = self._match_multiple_versions_with_translations_project(
                parent_project=parent_project,
                path=path,
                external_version_slug=external_version_slug,
            )
            if response:
                return response

        # Subprojects.
        if check_subprojects:
            response = self._match_subproject(
                parent_project=parent_project,
                path=path,
                external_version_slug=external_version_slug,
            )
            if response:
                return response

        # Single language project.
        if parent_project.versioning_scheme == MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS:
            response = self._match_multiple_versions_without_translations_project(
                parent_project=parent_project,
                path=path,
                external_version_slug=external_version_slug,
            )
            if response:
                return response

        # Single version project.
        if parent_project.versioning_scheme == SINGLE_VERSION_WITHOUT_TRANSLATIONS:
            response = self._match_single_version_without_translations_project(
                parent_project=parent_project,
                path=path,
                external_version_slug=external_version_slug,
            )
            if response:
                return response

        raise InvalidPathForVersionedProjectError(
            project=parent_project,
            path=self._normalize_filename(path),
        )

    @staticmethod
    def get_domain_from_host(host):
        """
        Get the normalized domain from a hostname.

        A hostname can include the port.
        """
        return host.lower().split(":")[0]

    def unresolve_domain(self, domain):
        """
        Unresolve domain by extracting relevant information from it.

        :param str domain: Domain to extract the information from.
         It can be a full URL, in that case, only the domain is used.
        :returns: A UnresolvedDomain object.
        """
        parsed_domain = urlparse(domain)
        if parsed_domain.scheme:
            if parsed_domain.scheme not in ["http", "https"]:
                raise InvalidSchemeError(parsed_domain.scheme)
            domain = parsed_domain.hostname

        if not domain:
            raise InvalidSubdomainError(domain)

        public_domain = self.get_domain_from_host(settings.PUBLIC_DOMAIN)
        external_domain = self.get_domain_from_host(settings.RTD_EXTERNAL_VERSION_DOMAIN)

        subdomain, *root_domain = domain.split(".", maxsplit=1)
        root_domain = root_domain[0] if root_domain else ""

        # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`.
        if public_domain == root_domain:
            project_slug = subdomain
            log.debug("Public domain.", domain=domain)
            return UnresolvedDomain(
                source_domain=domain,
                source=DomainSourceType.public_domain,
                project=self._resolve_project_slug(project_slug, domain),
            )

        # Serve from the RTD_EXTERNAL_VERSION_DOMAIN, ensuring it looks like
        # `project--version.RTD_EXTERNAL_VERSION_DOMAIN`.
        if external_domain == root_domain:
            try:
                project_slug, version_slug = subdomain.rsplit("--", maxsplit=1)
                log.debug("External versions domain.", domain=domain)
                return UnresolvedDomain(
                    source_domain=domain,
                    source=DomainSourceType.external_domain,
                    project=self._resolve_project_slug(project_slug, domain),
                    external_version_slug=version_slug,
                )
            except ValueError as exc:
                log.info("Invalid format of external versions domain.", domain=domain)
                raise InvalidExternalDomainError(domain=domain) from exc

        if public_domain in domain or external_domain in domain:
            # NOTE: This can catch some possibly valid domains (docs.readthedocs.io.com)
            # for example, but these might be phishing, so let's block them for now.
            log.debug("Weird variation of our domain.", domain=domain)
            raise SuspiciousHostnameError(domain=domain)

        # Custom domain.
        domain_object = Domain.objects.filter(domain=domain).select_related("project").first()
        if not domain_object:
            log.info("Invalid domain.", domain=domain)
            raise InvalidCustomDomainError(domain=domain)

        log.debug("Custom domain.", domain=domain)
        return UnresolvedDomain(
            source_domain=domain,
            source=DomainSourceType.custom_domain,
            project=domain_object.project,
            domain=domain_object,
        )

    def _resolve_project_slug(self, slug, domain):
        """Get the project from the slug or raise an exception if not found."""
        try:
            return Project.objects.get(slug=slug)
        except Project.DoesNotExist as exc:
            raise InvalidSubdomainError(domain=domain) from exc

    def unresolve_domain_from_request(self, request):
        """
        Unresolve domain by extracting relevant information from the request.

        We first check if the ``X-RTD-Slug`` header has been set for explicit
        project mapping, otherwise we unresolve by calling `self.unresolve_domain`
        on the host.

        :param request: Request to extract the information from.
        :returns: A UnresolvedDomain object.
        """
        host = self.get_domain_from_host(request.get_host())
        structlog.contextvars.bind_contextvars(host=host)

        # Explicit Project slug being passed in.
        header_project_slug = request.headers.get("X-RTD-Slug", "").lower()
        if header_project_slug:
            project = Project.objects.filter(
                slug=header_project_slug,
                feature__feature_id=Feature.RESOLVE_PROJECT_FROM_HEADER,
            ).first()
            if project:
                log.info(
                    "Setting project based on X_RTD_SLUG header.",
                    project_slug=project.slug,
                )
                return UnresolvedDomain(
                    source_domain=host,
                    source=DomainSourceType.http_header,
                    project=project,
                )
            log.warning(
                "X-RTD-Header passed for project without it enabled.",
                project_slug=header_project_slug,
            )
            raise InvalidXRTDSlugHeaderError

        return unresolver.unresolve_domain(host)


unresolver = Unresolver()
unresolve = unresolver.unresolve_url
