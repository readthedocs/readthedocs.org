"""Views for doc serving."""
import itertools
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import resolve as url_resolve
from django.views import View

from readthedocs.analytics.models import PageView
from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.builds.constants import EXTERNAL, INTERNAL, LATEST, STABLE
from readthedocs.builds.models import Version
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.resolver import resolve_path
from readthedocs.core.unresolver import (
    InvalidExternalVersionError,
    InvalidPathForVersionedProjectError,
    TranslationNotFoundError,
    VersionNotFoundError,
    unresolver,
)
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects import constants
from readthedocs.projects.models import Domain, Feature, ProjectRelationship
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.proxito.constants import RedirectType
from readthedocs.proxito.exceptions import (
    ProxitoHttp404,
    ProxitoProjectHttp404,
    ProxitoProjectPageHttp404,
    ProxitoProjectVersionHttp404,
    ProxitoSubProjectHttp404,
)
from readthedocs.redirects.exceptions import InfiniteRedirectException
from readthedocs.storage import build_media_storage

from .mixins import (
    InvalidPathError,
    ServeDocsMixin,
    ServeRedirectMixin,
    StorageFileNotFound,
)
from .utils import _get_project_data_from_request

log = structlog.get_logger(__name__)  # noqa


class ServePageRedirect(CDNCacheControlMixin, ServeRedirectMixin, ServeDocsMixin, View):
    def get(self, request, subproject_slug=None, filename=""):

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project
        parent_project = project

        # Use the project from the domain, or use the subproject slug.
        if subproject_slug:
            try:
                project = project.subprojects.get(alias=subproject_slug).child
            except ProjectRelationship.DoesNotExist:
                raise ProxitoSubProjectHttp404(
                    f"Did not find subproject slug {subproject_slug} for project {project.slug}",
                    project=parent_project,
                    project_slug=parent_project.slug,
                    subproject_slug=subproject_slug,
                    proxito_path=request.proxito_path,
                )

        # Get the default version from the current project,
        # or the version from the external domain.
        if unresolved_domain.is_from_external_domain:
            version_slug = unresolved_domain.external_version_slug
        else:
            version_slug = project.get_default_version()

        # TODO: find a better way to pass this to the middleware.
        request.path_project_slug = project.slug

        return self.system_redirect(
            request=request,
            final_project=project,
            version_slug=version_slug,
            filename=filename,
            is_external_version=unresolved_domain.is_from_external_domain,
        )


class ServeDocsBase(CDNCacheControlMixin, ServeRedirectMixin, ServeDocsMixin, View):
    def get(
        self,
        request,
        project_slug=None,
        subproject_slug=None,
        subproject_slash=None,
        lang_slug=None,
        version_slug=None,
        filename="",
    ):
        """
        Take the incoming parsed URL's and figure out what file to serve.

        ``subproject_slash`` is used to determine if the subproject URL has a slash,
        so that we can decide if we need to serve docs or add a /.
        """
        unresolved_domain = request.unresolved_domain
        # Handle requests that need canonicalizing first,
        # e.g. HTTP -> HTTPS, redirect to canonical domain, etc.
        # We run this here to reduce work we need to do on easily cached responses.
        # It's slower for the end user to have multiple HTTP round trips,
        # but reduces chances for URL resolving bugs,
        # and makes caching more effective because we don't care about authz.
        redirect_type = self._get_canonical_redirect_type(request)
        if redirect_type:
            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = unresolved_domain.project.slug
            try:
                return self.canonical_redirect(
                    request=request,
                    final_project=unresolved_domain.project,
                    external_version_slug=unresolved_domain.external_version_slug,
                    redirect_type=redirect_type,
                )
            except InfiniteRedirectException:
                # ``canonical_redirect`` raises this when it's redirecting back to itself.
                # We can safely ignore it here because it's logged in ``canonical_redirect``,
                # and we don't want to issue infinite redirects.
                pass

        if unresolved_domain.project.has_feature(Feature.USE_UNRESOLVER_WITH_PROXITO):
            return self.get_using_unresolver(request)

        original_version_slug = version_slug
        version_slug = self.get_version_from_host(request, version_slug)

        try:
            (
                final_project,
                lang_slug,
                version_slug,
                filename,
            ) = _get_project_data_from_request(  # noqa
                request,
                project_slug=project_slug,
                subproject_slug=subproject_slug,
                lang_slug=lang_slug,
                version_slug=version_slug,
                filename=filename,
            )
        # This special treatment of ProxitoProjectHttp404 happens because the decorator that
        # resolves a project doesn't know if it's resolving a subproject or a normal project
        except ProxitoProjectHttp404 as e:
            if subproject_slug:
                log.debug("Project expected to be a subproject was not found")
                raise ProxitoSubProjectHttp404(
                    f"Could not find subproject for {subproject_slug}",
                    project_slug=e.project_slug,
                    subproject_slug=subproject_slug,
                )
            raise
        version = final_project.versions.filter(slug=version_slug).first()

        is_external = unresolved_domain.is_from_external_domain
        if (
            is_external
            and original_version_slug
            and original_version_slug != version_slug
        ):
            raise Http404("Version doesn't match the version from the domain.")

        manager = EXTERNAL if is_external else INTERNAL
        version = (
            final_project.versions(manager=manager).filter(slug=version_slug).first()
        )

        log.bind(
            project_slug=final_project.slug,
            subproject_slug=subproject_slug,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
            external=is_external,
        )

        # Skip serving versions that are not active (return 404). This is to
        # avoid serving files that we have in the storage, but its associated
        # version does not exist anymore or it was de-activated.
        #
        # Note that we want to serve the page when `version is None` because it
        # could be a valid URL, like `/` or `` (empty) that does not have a
        # version associated to it.
        #
        # However, if there is a `version_slug` in the URL but there is no
        # version on the database we want to return 404.
        if (version and not version.active) or (version_slug and not version):
            log.warning("Version does not exist or is not active.")
            raise ProxitoHttp404("Version does not exist or is not active.")

        if version:
            # All public versions can be cached.
            self.cache_response = version.is_public

        log.bind(cache_response=self.cache_response)
        log.debug('Serving docs.')

        # Verify if the project is marked as spam and return a 401 in that case
        spam_response = self._spam_response(request, final_project)
        if spam_response:
            # If a project was marked as spam,
            # all of their responses can be cached.
            self.cache_response = True
            return spam_response

        # Handle a / redirect when we aren't a single version
        if all([
                lang_slug is None,
                # External versions/builds will always have a version,
                # because it is taken from the host name
                version_slug is None or is_external,
                filename == '',
                not final_project.single_version,
        ]):
            return self.system_redirect(
                request=request,
                final_project=final_project,
                version_slug=version_slug,
                filename=filename,
                is_external_version=is_external,
            )

        # Handle `/projects/subproject` URL redirection:
        # when there _is_ a subproject_slug but not a subproject_slash
        if all([
                final_project.single_version,
                filename == '',
                subproject_slug,
                not subproject_slash,
        ]):
            return self.system_redirect(
                request=request,
                final_project=final_project,
                version_slug=version_slug,
                filename=filename,
                is_external_version=is_external,
            )

        if all([
                (lang_slug is None or version_slug is None),
                not final_project.single_version,
                self.version_type != EXTERNAL,
        ]):
            log.debug(
                'Invalid URL for project with versions.',
                filename=filename,
            )
            raise ProxitoHttp404("Invalid URL for project with versions")

        redirect_path, http_status = self.get_redirect(
            project=final_project,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
            full_path=request.path,
            forced_only=True,
        )
        if redirect_path and http_status:
            log.bind(forced_redirect=True)
            try:
                return self.get_redirect_response(
                    request=request,
                    redirect_path=redirect_path,
                    proxito_path=request.path,
                    http_status=http_status,
                )
            except InfiniteRedirectException:
                # Continue with our normal serve.
                pass

        # Check user permissions and return an unauthed response if needed
        if not self.allowed_user(request, final_project, version_slug):
            return self.get_unauthed_response(request, final_project)

        return self._serve_docs(
            request=request,
            project=final_project,
            version=version,
            filename=filename,
        )

    def _get_canonical_redirect_type(self, request):
        """If the current request needs a redirect, return the type of redirect to perform."""
        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project
        if unresolved_domain.is_from_custom_domain:
            domain = unresolved_domain.domain
            if domain.https and not request.is_secure():
                # Redirect HTTP -> HTTPS (302) for this custom domain.
                log.debug("Proxito CNAME HTTPS Redirect.", domain=domain.domain)
                return RedirectType.http_to_https

        # Check for subprojects before checking for canonical domains,
        # so we can redirect to the main domain first.
        # Custom domains on subprojects are not supported.
        if project.is_subproject:
            log.debug(
                "Proxito Public Domain -> Subproject Main Domain Redirect.",
                project_slug=project.slug,
            )
            return RedirectType.subproject_to_main_domain

        if unresolved_domain.is_from_public_domain:
            canonical_domain = (
                Domain.objects.filter(project=project)
                .filter(canonical=True, https=True)
                .exists()
            )
            if canonical_domain:
                log.debug(
                    "Proxito Public Domain -> Canonical Domain Redirect.",
                    project_slug=project.slug,
                )
                return RedirectType.to_canonical_domain

        return None

    def get_using_unresolver(self, request):
        """
        Resolve the current request using the new proxito implementation.

        This is basically a copy of the get() method,
        but adapted to make use of the unresolved to extract the current project, version, and file.
        """
        unresolved_domain = request.unresolved_domain
        # TODO: We shouldn't use path_info to the get the proxito path,
        # it should be captured in proxito/urls.py.
        path = request.path_info

        # We force all storage calls to use the external versions storage,
        # since we are serving an external version.
        if unresolved_domain.is_from_external_domain:
            self.version_type = EXTERNAL

        try:
            unresolved = unresolver.unresolve_path(
                unresolved_domain=unresolved_domain,
                path=path,
                append_indexhtml=False,
            )
        except VersionNotFoundError as exc:
            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = exc.project.slug
            request.path_version_slug = exc.version_slug
            raise Http404
        except InvalidExternalVersionError as exc:
            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = exc.project.slug
            request.path_version_slug = exc.external_version_slug
            raise Http404
        except TranslationNotFoundError as exc:
            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = exc.project.slug
            raise Http404
        except InvalidPathForVersionedProjectError as exc:
            project = exc.project
            if unresolved_domain.is_from_external_domain:
                version_slug = unresolved_domain.external_version_slug
            else:
                version_slug = None

            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = project.slug
            request.path_version_slug = version_slug

            if exc.path == "/":
                # When the path is empty, the project didn't have an explicit version,
                # so we need to redirect to the default version.
                # This is `/ -> /en/latest/` or
                # `/projects/subproject/ -> /projects/subproject/en/latest/`.
                return self.system_redirect(
                    request=request,
                    final_project=project,
                    version_slug=version_slug,
                    filename=exc.path,
                    is_external_version=unresolved_domain.is_from_external_domain,
                )

            raise Http404

        project = unresolved.project
        version = unresolved.version
        filename = unresolved.filename

        log.bind(
            project_slug=project.slug,
            version_slug=version.slug,
            filename=filename,
            external=unresolved_domain.is_from_external_domain,
        )

        # TODO: find a better way to pass this to the middleware.
        request.path_project_slug = project.slug
        request.path_version_slug = version.slug

        if not version.active:
            log.warning("Version is not active.")
            raise Http404("Version is not active.")

        # All public versions can be cached.
        self.cache_response = version.is_public

        log.bind(cache_response=self.cache_response)
        log.debug("Serving docs.")

        # Verify if the project is marked as spam and return a 401 in that case
        spam_response = self._spam_response(request, project)
        if spam_response:
            # If a project was marked as spam,
            # all of their responses can be cached.
            self.cache_response = True
            return spam_response

        # Trailing slash redirect.
        # We don't want to serve documentation at:
        # - `/en/latest`
        # - `/projects/subproject/en/latest`
        # - `/projects/subproject`
        # These paths need to end with an slash.
        if filename == "/" and not path.endswith("/"):
            # TODO: We could avoid calling the resolver,
            # and just redirect to the same path with a slash.
            return self.system_redirect(
                request=request,
                final_project=project,
                version_slug=version.slug,
                filename=filename,
                is_external_version=unresolved_domain.is_from_external_domain,
            )

        # Check for forced redirects.
        redirect_path, http_status = self.get_redirect(
            project=project,
            lang_slug=project.language,
            version_slug=version.slug,
            filename=filename,
            full_path=request.path,
            forced_only=True,
        )
        if redirect_path and http_status:
            log.bind(forced_redirect=True)
            try:
                return self.get_redirect_response(
                    request=request,
                    redirect_path=redirect_path,
                    proxito_path=request.path,
                    http_status=http_status,
                )
            except InfiniteRedirectException:
                # Continue with our normal serve.
                pass

        # Check user permissions and return an unauthed response if needed.
        if not self.allowed_user(request, project, version.slug):
            return self.get_unauthed_response(request, project)

        return self._serve_docs(
            request=request,
            project=project,
            version=version,
            filename=filename,
        )


class ServeDocs(SettingsOverrideObject):
    _default_class = ServeDocsBase


class ServeError404Base(ServeRedirectMixin, ServeDocsMixin, View):

    def get(self, request, proxito_path, template_name='404.html'):
        """
        Handler for 404 pages on subdomains.

        This does a couple of things:

        * Handles directory indexing for URLs that don't end in a slash
        * Handles directory indexing for README.html (for now)
        * Check for user redirects
        * Record the broken link for analytics
        * Handles custom 404 serving

        For 404's, first search for a 404 page in the current version, then continues
        with the default version and finally, if none of them are found, the Read
        the Docs default page (Maze Found) is rendered by Django and served.
        """
        log.bind(proxito_path=proxito_path)
        log.debug('Executing 404 handler.')

        unresolved_domain = request.unresolved_domain
        if unresolved_domain.project.has_feature(Feature.USE_UNRESOLVER_WITH_PROXITO):
            return self.get_using_unresolver(request, proxito_path)

        # Parse the URL using the normal urlconf, so we get proper subdomain/translation data
        _, __, kwargs = url_resolve(
            proxito_path,
            urlconf='readthedocs.proxito.urls',
        )

        version_slug = kwargs.get('version_slug')
        version_slug = self.get_version_from_host(request, version_slug)
        # This special treatment of ProxitoProjectHttp404 happens because the decorator that
        # resolves a project doesn't know if it's resolving a subproject or a normal project
        subproject_slug = kwargs.get("subproject_slug")
        project_slug = kwargs.get("project_slug")
        try:
            (
                final_project,
                lang_slug,
                version_slug,
                filename,
            ) = _get_project_data_from_request(  # noqa
                request,
                project_slug,
                subproject_slug,
                lang_slug=kwargs.get("lang_slug"),
                version_slug=version_slug,
                filename=kwargs.get("filename", ""),
            )
        except ProxitoProjectHttp404 as e:
            if subproject_slug:
                log.debug("Project expected to be a subproject was not found")
                raise ProxitoSubProjectHttp404(
                    f"Could not find subproject for {subproject_slug}",
                    project_slug=e.project_slug,
                    subproject_slug=subproject_slug,
                    proxito_path=proxito_path,
                )
            raise

        log.bind(
            project_slug=final_project.slug,
            version_slug=version_slug,
        )

        version = Version.objects.filter(
            project=final_project, slug=version_slug
        ).first()
        version_found = bool(version)

        # If we were able to resolve to a valid version, it means that the
        # current file doesn't exist. So we check if we can redirect to its
        # index file if it exists before doing anything else.
        if version:
            response = self._get_index_file_redirect(
                request=request,
                project=final_project,
                version=version,
                filename=filename,
                full_path=proxito_path,
            )

            if response:
                return response

        # Check and perform redirects on 404 handler
        # NOTE: this redirect check must be done after trying files like
        # ``index.html`` and ``README.html`` to emulate the behavior we had when
        # serving directly from NGINX without passing through Python.
        redirect_path, http_status = self.get_redirect(
            project=final_project,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
            full_path=proxito_path,
        )
        if redirect_path and http_status:
            try:
                return self.get_redirect_response(request, redirect_path, proxito_path, http_status)
            except InfiniteRedirectException:
                # ``get_redirect_response`` raises this when it's redirecting back to itself.
                # We can safely ignore it here because it's logged in ``canonical_redirect``,
                # and we don't want to issue infinite redirects.
                pass

        # Register 404 pages into our database for user's analytics
        self._register_broken_link(
            project=final_project,
            version=version,
            path=filename,
            full_path=proxito_path,
        )

        response = self._get_custom_404_page(
            request=request,
            project=final_project,
            version=version,
        )
        if response:
            return response

        if version_found:
            raise ProxitoProjectPageHttp404(
                "Page not found and no custom 404",
                project=final_project,
                project_slug=final_project.slug,
                proxito_path=proxito_path,
            )
        elif kwargs.get("subproject_slug"):
            raise ProxitoSubProjectHttp404(
                "Subproject not found and no custom 404",
                project=final_project,
                project_slug=final_project.slug,
                subproject_slug=kwargs.get("subproject_slug"),
                proxito_path=proxito_path,
            )
        else:
            raise ProxitoProjectVersionHttp404(
                "Version not found and no custom 404",
                project=final_project,
                project_slug=final_project.slug,
                proxito_path=proxito_path,
            )

    def _register_broken_link(self, project, version, path, full_path):
        try:
            if not project.has_feature(Feature.RECORD_404_PAGE_VIEWS):
                return

            # This header is set from Cloudflare,
            # it goes from 0 to 100, 0 being low risk,
            # and values above 10 are bots/spammers.
            # https://developers.cloudflare.com/ruleset-engine/rules-language/fields/#dynamic-fields.
            threat_score = int(self.request.headers.get("X-Cloudflare-Threat-Score", 0))
            if threat_score > 10:
                log.info(
                    "Suspicious threat score, not recording 404.",
                    threat_score=threat_score,
                )
                return

            # If the path isn't attached to a version
            # it should be the same as the full_path,
            # otherwise it would be empty.
            if not version:
                path = full_path
            PageView.objects.register_page_view(
                project=project,
                version=version,
                path=path,
                full_path=full_path,
                status=404,
            )
        except Exception:
            # Don't break doc serving if there was an error
            # while recording the broken link.
            log.exception(
                "Error while recording the broken link",
                project_slug=project.slug,
                full_path=full_path,
            )

    def _get_custom_404_page(self, request, project, version=None):
        """
        Try to serve a custom 404 page from this project.

        If a version is given, try to serve the 404 page from that version first,
        if it doesn't exist, try to serve the 404 page from the default version.

        We check for a 404.html or 404/index.html file.

        If a 404 page is found, we return a response with the content of that file,
        `None` otherwise.
        """
        current_version_slug = version.slug if version else None
        versions_slug = []
        if current_version_slug:
            versions_slug.append(current_version_slug)

        default_version_slug = project.get_default_version()
        if default_version_slug != current_version_slug:
            versions_slug.append(default_version_slug)

        for version_slug_404 in versions_slug:
            if not self.allowed_user(request, project, version_slug_404):
                continue

            storage_root_path = project.get_storage_path(
                type_="html",
                version_slug=version_slug_404,
                include_file=False,
                version_type=self.version_type,
            )
            tryfiles = ["404.html", "404/index.html"]
            for tryfile in tryfiles:
                storage_filename_path = build_media_storage.join(
                    storage_root_path, tryfile
                )
                if build_media_storage.exists(storage_filename_path):
                    log.info(
                        "Serving custom 404.html page.",
                        version_slug_404=version_slug_404,
                        storage_filename_path=storage_filename_path,
                    )
                    resp = HttpResponse(
                        build_media_storage.open(storage_filename_path).read()
                    )
                    resp.status_code = 404
                    return resp
        return None

    def _get_index_file_redirect(self, request, project, version, filename, full_path):
        """Check if a file is a directory and redirect to its index/README file."""
        storage_root_path = project.get_storage_path(
            type_="html",
            version_slug=version.slug,
            include_file=False,
            version_type=self.version_type,
        )

        # First, check for dirhtml with slash
        for tryfile in ("index.html", "README.html"):
            storage_filename_path = build_media_storage.join(
                storage_root_path,
                f"{filename}/{tryfile}".lstrip("/"),
            )
            log.debug("Trying index filename.")
            if build_media_storage.exists(storage_filename_path):
                log.info("Redirecting to index file.", tryfile=tryfile)
                # Use urlparse so that we maintain GET args in our redirect
                parts = urlparse(full_path)
                if tryfile == "README.html":
                    new_path = parts.path.rstrip("/") + f"/{tryfile}"
                else:
                    new_path = parts.path.rstrip("/") + "/"

                # `full_path` doesn't include query params.`
                query = urlparse(request.get_full_path()).query
                redirect_url = parts._replace(
                    path=new_path,
                    query=query,
                ).geturl()

                # TODO: decide if we need to check for infinite redirect here
                # (from URL == to URL)
                return HttpResponseRedirect(redirect_url)

        return None

    def get_using_unresolver(self, request, path):
        """
        404 handler using the new proxito implementation.

        This is basically a copy of the get() method, but adapted to make use
        of the unresolver to extract the current project, version, and file.
        """
        unresolved_domain = request.unresolved_domain
        # We force all storage calls to use the external versions storage,
        # since we are serving an external version.
        if unresolved_domain.is_from_external_domain:
            self.version_type = EXTERNAL

        project = None
        version = None
        filename = None
        lang_slug = None
        version_slug = None
        # Try to map the current path to a project/version/filename.
        # If that fails, we fill the variables with the information we have
        # available in the exceptions.
        try:
            unresolved = unresolver.unresolve_path(
                unresolved_domain=unresolved_domain,
                path=path,
                append_indexhtml=False,
            )
            project = unresolved.project
            version = unresolved.version
            filename = unresolved.filename
            lang_slug = project.language
            version_slug = version.slug
        except VersionNotFoundError as exc:
            project = exc.project
            lang_slug = project.language
            version_slug = exc.version_slug
            filename = exc.filename
        except TranslationNotFoundError as exc:
            project = exc.project
            lang_slug = exc.language
            version_slug = exc.version_slug
            filename = exc.filename
        except InvalidExternalVersionError as exc:
            project = exc.project
        except InvalidPathForVersionedProjectError as exc:
            project = exc.project
            filename = exc.path

        log.bind(
            project_slug=project.slug,
            version_slug=version_slug,
        )

        # TODO: find a better way to pass this to the middleware.
        request.path_project_slug = project.slug
        request.path_version_slug = version_slug

        # If we were able to resolve to a valid version, it means that the
        # current file doesn't exist. So we check if we can redirect to its
        # index file if it exists before doing anything else.
        if version:
            response = self._get_index_file_redirect(
                request=request,
                project=project,
                version=version,
                filename=filename,
                full_path=path,
            )
            if response:
                return response

        # Check and perform redirects on 404 handler
        # NOTE: this redirect check must be done after trying files like
        # ``index.html`` and ``README.html`` to emulate the behavior we had when
        # serving directly from NGINX without passing through Python.
        redirect_path, http_status = self.get_redirect(
            project=project,
            lang_slug=lang_slug,
            version_slug=version_slug,
            filename=filename,
            full_path=path,
        )
        if redirect_path and http_status:
            try:
                return self.get_redirect_response(
                    request, redirect_path, path, http_status
                )
            except InfiniteRedirectException:
                # ``get_redirect_response`` raises this when it's redirecting back to itself.
                # We can safely ignore it here because it's logged in ``canonical_redirect``,
                # and we don't want to issue infinite redirects.
                pass

        # Register 404 pages into our database for user's analytics
        self._register_broken_link(
            project=project,
            version=version,
            path=filename,
            full_path=path,
        )

        response = self._get_custom_404_page(
            request=request,
            project=project,
            version=version,
        )
        if response:
            return response
        raise Http404("No custom 404 page found.")


class ServeError404(SettingsOverrideObject):
    _default_class = ServeError404Base


class ServeRobotsTXTBase(ServeDocsMixin, View):

    # Always cache this view, since it's the same for all users.
    cache_response = True

    def get(self, request):
        """
        Serve custom user's defined ``/robots.txt``.

        If the project is delisted or is a spam project, we force a special robots.txt.

        If the user added a ``robots.txt`` in the "default version" of the
        project, we serve it directly.
        """
        project = request.unresolved_domain.project

        if project.delisted:
            return render(
                request,
                "robots.delisted.txt",
                content_type="text/plain",
            )

        # Verify if the project is marked as spam and return a custom robots.txt
        elif "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import is_robotstxt_denied  # noqa
            if is_robotstxt_denied(project):
                return render(
                    request,
                    'robots.spam.txt',
                    content_type='text/plain',
                )

        # Use the ``robots.txt`` file from the default version configured
        version_slug = project.get_default_version()
        version = project.versions.get(slug=version_slug)

        no_serve_robots_txt = any([
            # If the default version is private or,
            version.privacy_level == constants.PRIVATE,
            # default version is not active or,
            not version.active,
            # default version is not built
            not version.built,
        ])

        if no_serve_robots_txt:
            # ... we do return a 404
            raise ProxitoHttp404()

        log.bind(
            project_slug=project.slug,
            version_slug=version.slug,
        )

        try:
            response = self._serve_docs(
                request=request,
                project=project,
                version=version,
                filename="robots.txt",
                check_if_exists=True,
            )
            log.info('Serving custom robots.txt file.')
            return response
        except StorageFileNotFound:
            pass

        # Serve default robots.txt
        sitemap_url = '{scheme}://{domain}/sitemap.xml'.format(
            scheme='https',
            domain=project.subdomain(),
        )
        context = {
            'sitemap_url': sitemap_url,
            'hidden_paths': self._get_hidden_paths(project),
        }
        return render(
            request,
            'robots.txt',
            context,
            content_type='text/plain',
        )

    def _get_hidden_paths(self, project):
        """Get the absolute paths of the public hidden versions of `project`."""
        hidden_versions = (
            Version.internal.public(project=project)
            .filter(hidden=True)
        )
        hidden_paths = [
            resolve_path(project, version_slug=version.slug)
            for version in hidden_versions
        ]
        return hidden_paths


class ServeRobotsTXT(SettingsOverrideObject):
    _default_class = ServeRobotsTXTBase


class ServeSitemapXMLBase(View):

    # Always cache this view, since it's the same for all users.
    cache_response = True

    def get(self, request):
        """
        Generate and serve a ``sitemap.xml`` for a particular ``project``.

        The sitemap is generated from all the ``active`` and public versions of
        ``project``. These versions are sorted by using semantic versioning
        prepending ``latest`` and ``stable`` (if they are enabled) at the beginning.

        Following this order, the versions are assigned priorities and change
        frequency. Starting from 1 and decreasing by 0.1 for priorities and starting
        from daily, weekly to monthly for change frequency.

        If the project doesn't have any public version, the view raises ``Http404``.

        :param request: Django request object
        :param project: Project instance to generate the sitemap

        :returns: response with the ``sitemap.xml`` template rendered

        :rtype: django.http.HttpResponse
        """
        # pylint: disable=too-many-locals

        def priorities_generator():
            """
            Generator returning ``priority`` needed by sitemap.xml.

            It generates values from 1 to 0.1 by decreasing in 0.1 on each
            iteration. After 0.1 is reached, it will keep returning 0.1.
            """
            priorities = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            yield from itertools.chain(priorities, itertools.repeat(0.1))

        def hreflang_formatter(lang):
            """
            sitemap hreflang should follow correct format.

            Use hyphen instead of underscore in language and country value.
            ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
            """
            if '_' in lang:
                return lang.replace('_', '-')
            return lang

        def changefreqs_generator():
            """
            Generator returning ``changefreq`` needed by sitemap.xml.

            It returns ``weekly`` on first iteration, then ``daily`` and then it
            will return always ``monthly``.

            We are using ``monthly`` as last value because ``never`` is too
            aggressive. If the tag is removed and a branch is created with the same
            name, we will want bots to revisit this.
            """
            changefreqs = ['weekly', 'daily']
            yield from itertools.chain(changefreqs, itertools.repeat('monthly'))

        project = request.unresolved_domain.project
        public_versions = Version.internal.public(
            project=project,
            only_active=True,
        )
        if not public_versions.exists():
            raise ProxitoHttp404()

        sorted_versions = sort_version_aware(public_versions)

        # This is a hack to swap the latest version with
        # stable version to get the stable version first in the sitemap.
        # We want stable with priority=1 and changefreq='weekly' and
        # latest with priority=0.9 and changefreq='daily'
        # More details on this: https://github.com/rtfd/readthedocs.org/issues/5447
        if (len(sorted_versions) >= 2 and sorted_versions[0].slug == LATEST and
                sorted_versions[1].slug == STABLE):
            sorted_versions[0], sorted_versions[1] = sorted_versions[1], sorted_versions[0]

        versions = []
        for version, priority, changefreq in zip(
                sorted_versions,
                priorities_generator(),
                changefreqs_generator(),
        ):
            element = {
                'loc': version.get_subdomain_url(),
                'priority': priority,
                'changefreq': changefreq,
                'languages': [],
            }

            # Version can be enabled, but not ``built`` yet. We want to show the
            # link without a ``lastmod`` attribute
            last_build = version.builds.order_by('-date').first()
            if last_build:
                element['lastmod'] = last_build.date.isoformat()

            if project.translations.exists():
                for translation in project.translations.all():
                    translation_versions = (
                        Version.internal.public(project=translation
                                                ).values_list('slug', flat=True)
                    )
                    if version.slug in translation_versions:
                        href = project.get_docs_url(
                            version_slug=version.slug,
                            lang_slug=translation.language,
                        )
                        element['languages'].append({
                            'hreflang': hreflang_formatter(translation.language),
                            'href': href,
                        })

                # Add itself also as protocol requires
                element['languages'].append({
                    'hreflang': project.language,
                    'href': element['loc'],
                })

            versions.append(element)

        context = {
            'versions': versions,
        }
        return render(
            request,
            'sitemap.xml',
            context,
            content_type='application/xml',
        )


class ServeSitemapXML(SettingsOverrideObject):
    _default_class = ServeSitemapXMLBase


class ServeStaticFiles(CDNCacheControlMixin, CDNCacheTagsMixin, ServeDocsMixin, View):

    """
    Serve static files from the same domain the docs are being served from.

    This is basically a proxy for ``STATIC_URL``.
    """

    project_cache_tag = "rtd-staticfiles"

    # This view can always be cached,
    # since these are static files used for all projects.
    cache_response = True

    def get(self, request, filename):
        try:
            return self._serve_static_file(request=request, filename=filename)
        except InvalidPathError:
            raise Http404

    def _get_cache_tags(self):
        """
        Add an additional *global* tag.

        This is so we can purge all files from all projects
        with one single call.
        """
        tags = super()._get_cache_tags()
        tags.append(self.project_cache_tag)
        return tags

    def _get_project(self):
        # Method used by the CDNCacheTagsMixin class.
        return self.request.unresolved_domain.project

    def _get_version(self):
        # This view isn't attached to a version.
        return None
