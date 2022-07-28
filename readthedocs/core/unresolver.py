import re
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog
from django.conf import settings

from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.constants import LANGUAGES
from readthedocs.projects.models import Domain, Project

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class UnresolvedURL:
    canonical_project: Project
    project: Project
    version: Version = None
    file: str = None
    fragment: str = None
    domain: Domain = None
    external: bool = False


class UnresolverBase:

    LANGUAGES_CODES = {code for code, _ in LANGUAGES}

    def unresolve(self, url):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.split(":", maxsplit=1)[0]
        project_slug, domain_object, external = self._unresolve_domain(domain)
        if not project_slug:
            return None

        canonical_project = Project.objects.filter(slug=project_slug).first()
        if not canonical_project:
            return None

        project, version, file = self._unresolve_path(
            canonical_project=canonical_project,
            path=parsed.path,
        )
        if not project:
            return UnresolvedURL(
                canonical_project=canonical_project,
                project=canonical_project,
            )

        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if file == "":
            file = "/index.html"
        elif file and file.endswith("/"):
            file += "index.html"

        return UnresolvedURL(
            canonical_project=canonical_project,
            project=project,
            version=version,
            file=file,
            fragment=parsed.fragment,
            domain=domain_object,
            external=external,
        )

    def _unresolve_domain(self, domain):
        """
        Unresolve domain.

        We extract the project slug from the domain.

        :return: A tuple with the project slug and domain object if the domain is from a custom domain.
        """
        public_domain = settings.PUBLIC_DOMAIN.lower().split(":")[0]
        external_domain = settings.RTD_EXTERNAL_VERSION_DOMAIN.lower().split(":")[0]

        domain_parts = domain.split(".")
        public_domain_parts = public_domain.split(".")
        external_domain_parts = external_domain.split(".")

        if public_domain in domain or domain == "proxito":
            # Serve from the PUBLIC_DOMAIN, ensuring it looks like `foo.PUBLIC_DOMAIN`
            if public_domain_parts == domain_parts[1:]:
                project_slug = domain_parts[0]
                return project_slug, None, False

            # TODO: This can catch some possibly valid domains (docs.readthedocs.io.com) for example,
            # but these feel like they might be phishing, etc. so let's ignore them for now.
            return None, None, False

        if external_domain in domain:
            # Serve custom versions on external-host-domain
            if external_domain_parts == domain_parts[1:]:
                try:
                    project_slug, _ = domain_parts[0].rsplit("--", 1)
                    return project_slug, None, True
                except ValueError:
                    return None, None, False

        # Serve CNAMEs
        domain_object = (
            Domain.objects.filter(domain=domain).prefetch_related("project").first()
        )
        if domain_object:
            project_slug = domain_object.project.slug
            return project_slug, domain_object, False

        return None, None, False

    def _unresolve_path(self, canonical_project, path, check_subprojects=True):
        # Multiversion project.
        versioned_pattern = re.compile(
            r"^/(?P<language>[^/]+)/?((?P<version>[^/]+)(?P<file>.*)?)?$"
        )
        # if canonical_project.pattern:
        #    versioned_pattern = canonical_project.project_urlconf
        match = versioned_pattern.match(path)
        if match:
            language = match.group("language")
            version_slug = match.group("version")
            file = match.group("file")
            if (
                not canonical_project.single_version
                and language in self.LANGUAGES_CODES
            ):
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

        # Subprojects.
        subproject_pattern = re.compile(r"^/projects/(?P<project>[^/]+)(?P<file>.*)?$")
        # if canonical_project.subproject_pattern:
        #    subproject_pattern = subproject_pattern
        match = subproject_pattern.match(path)
        if check_subprojects and match:
            project_slug = match.group("project")
            file = match.group("file")
            project_relationship = canonical_project.subprojects.filter(
                alias=project_slug
            ).first()
            if project_relationship:
                return self._unresolve_path(
                    canonical_project=project_relationship.child,
                    path=file,
                    check_subprojects=False,
                )

        # Single version.
        single_version_pattern = re.compile("^(?P<file>.+)$")
        # if canonical_project.pattern:
        #     single_version_pattern = canonical_project.pattern
        match = single_version_pattern.match(path)
        if canonical_project.single_version and match:
            file = match.group("file")
            version = canonical_project.versions.filter(
                slug=canonical_project.default_version
            ).first()
            if version:
                return canonical_project, version, file
            return canonical_project, None, None

        return None, None, None


class Unresolver(SettingsOverrideObject):

    _default_class = UnresolverBase


unresolver = Unresolver()
unresolve = unresolver.unresolve
