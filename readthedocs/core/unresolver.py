import structlog
from readthedocs.projects.constants import LANGUAGES
import re
from django.conf import settings
from collections import namedtuple
from urllib.parse import urlparse

from django.test.client import RequestFactory
from django.urls import resolve as url_resolve

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.proxito.middleware import map_host_to_project_slug
from readthedocs.proxito.views.mixins import ServeDocsMixin
from readthedocs.projects.models import Domain
from readthedocs.proxito.views.utils import _get_project_data_from_request

log = structlog.get_logger(__name__)

UnresolvedObject = namedtuple(
    'Unresolved', 'project, language_slug, version_slug, filename, fragment')


class UnresolverBase:

    LANGUAGES_CODES = {code for code, _ in LANGUAGES}

    def unresolve(self, url):
        """
        Turn a URL into the component parts that our views would use to process them.

        This is useful for lots of places,
        like where we want to figure out exactly what file a URL maps to.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.split(':', 1)[0]

        # TODO: Make this not depend on the request object,
        # but instead move all this logic here working on strings.
        request = RequestFactory().get(path=parsed.path, HTTP_HOST=domain)
        project_slug = map_host_to_project_slug(request)

        # Handle returning a response
        if hasattr(project_slug, 'status_code'):
            return None

        request.host_project_slug = request.slug = project_slug
        return self.unresolve_from_request(request, url)

    def unresolve_from_request(self, request, path):
        """
        Unresolve using a request.

        ``path`` can be a full URL, but the domain will be ignored,
        since that information is already in the request object.

        None is returned if the request isn't valid.
        """
        parsed = urlparse(path)
        path = parsed.path
        project_slug = getattr(request, 'host_project_slug', None)

        if not project_slug:
            return None

        _, __, kwargs = url_resolve(
            path,
            urlconf='readthedocs.proxito.urls',
        )

        mixin = ServeDocsMixin()
        version_slug = mixin.get_version_from_host(request, kwargs.get('version_slug'))

        final_project, lang_slug, version_slug, filename = _get_project_data_from_request(  # noqa
            request,
            project_slug=project_slug,
            subproject_slug=kwargs.get('subproject_slug'),
            lang_slug=kwargs.get('lang_slug'),
            version_slug=version_slug,
            filename=kwargs.get('filename', ''),
        )

        # Handle our backend storage not supporting directory indexes,
        # so we need to append index.html when appropriate.
        if not filename or filename.endswith('/'):
            # We need to add the index.html to find this actual file
            filename += 'index.html'

        log.debug(
            'Unresolver parsed.',
            project_slug=final_project.slug,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
        )
        return UnresolvedObject(final_project, lang_slug, version_slug, filename, parsed.fragment)

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
        file = match.group("file") or "/"

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
        file = match.group("file") or "/"
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

        file = match.group("file") or "/"
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
unresolve_from_request = unresolver.unresolve_from_request
