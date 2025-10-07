"""Views for doc serving."""

import itertools
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import View

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import STABLE
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.resolver import Resolver
from readthedocs.core.unresolver import InvalidExternalVersionError
from readthedocs.core.unresolver import InvalidPathForVersionedProjectError
from readthedocs.core.unresolver import TranslationNotFoundError
from readthedocs.core.unresolver import TranslationWithoutVersionError
from readthedocs.core.unresolver import VersionNotFoundError
from readthedocs.core.unresolver import unresolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.constants import OLD_LANGUAGES_CODE_MAPPING
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Domain
from readthedocs.projects.models import HTMLFile
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.proxito.constants import RedirectType
from readthedocs.proxito.exceptions import ContextualizedHttp404
from readthedocs.proxito.exceptions import ProjectFilenameHttp404
from readthedocs.proxito.exceptions import ProjectTranslationHttp404
from readthedocs.proxito.exceptions import ProjectVersionHttp404
from readthedocs.proxito.redirects import canonical_redirect
from readthedocs.proxito.views.mixins import InvalidPathError
from readthedocs.proxito.views.mixins import ServeDocsMixin
from readthedocs.proxito.views.mixins import ServeRedirectMixin
from readthedocs.proxito.views.mixins import StorageFileNotFound
from readthedocs.redirects.exceptions import InfiniteRedirectException
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)  # noqa


class ServePageRedirect(CDNCacheControlMixin, ServeRedirectMixin, ServeDocsMixin, View):
    """
    Page redirect view.

    This allows users to redirec to the default version of a project.
    For example:

    - /page/api/index.html -> /en/latest/api/index.html
    - /projects/subproject/page/index.html -> /projects/subproject/en/latest/api/index.html
    """

    def get(self, request, subproject_slug=None, filename=""):
        """Handle all page redirects."""

        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project

        # Use the project from the domain, or use the subproject slug.
        if subproject_slug:
            project = get_object_or_404(project.subprojects, alias=subproject_slug).child

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
    """
    Serve docs view.

    This view serves all the documentation pages,
    and handles canonical redirects.
    """

    def get(self, request, path):
        """
        Serve a file from the resolved project and version from the path.

        Before trying to serve the file, we check for canonical redirects.

        If the path isn't valid for the current project, or if the version/translation
        doesn't exist, we raise a 404. This will be handled by the ``ServeError404``
        view.

        This view handles the following redirects:

        - Redirect to the default version of the project
          from the root path or translation
          (/ -> /en/latest/, /en/ -> /en/latest/).
        - Trailing slash redirect (/en/latest -> /en/latest/).
        - Forced redirects (apply a user defined redirect even if the path exists).

        This view checks if the user is allowed to access the current version,
        and if the project is marked as spam.
        """
        unresolved_domain = request.unresolved_domain
        # Protect against bad requests to API hosts that don't set this attribute.
        if not unresolved_domain:
            raise Http404
        # Handle requests that need canonicalizing first,
        # e.g. HTTP -> HTTPS, redirect to canonical domain, etc.
        # We run this here to reduce work we need to do on easily cached responses.
        # It's slower for the end user to have multiple HTTP round trips,
        # but reduces chances for URL resolving bugs,
        # and makes caching more effective because we don't care about authz.
        redirect_type = self._get_canonical_redirect_type(request)
        if redirect_type:
            try:
                return canonical_redirect(
                    request,
                    project=unresolved_domain.project,
                    redirect_type=redirect_type,
                    external_version_slug=unresolved_domain.external_version_slug,
                )
            except InfiniteRedirectException:
                # ``canonical_redirect`` raises this when it's redirecting back to itself.
                # We can safely ignore it here because it's logged in ``canonical_redirect``,
                # and we don't want to issue infinite redirects.
                pass

        # Django doesn't include the leading slash in the path, so we normalize it here.
        path = "/" + path
        return self.serve_path(request, path)

    def _get_canonical_redirect_type(self, request):
        """If the current request needs a redirect, return the type of redirect to perform."""
        unresolved_domain = request.unresolved_domain
        project = unresolved_domain.project
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
                Domain.objects.filter(project=project).filter(canonical=True, https=True).exists()
            )
            # For .com we need to check if the project supports custom domains.
            if canonical_domain and Resolver()._use_cname(project):
                log.debug(
                    "Proxito Public Domain -> Canonical Domain Redirect.",
                    project_slug=project.slug,
                )
                return RedirectType.to_canonical_domain

        return None

    def serve_path(self, request, path):
        unresolved_domain = request.unresolved_domain

        # We force all storage calls to use the external versions storage,
        # since we are serving an external version.
        if unresolved_domain.is_from_external_domain:
            self.version_type = EXTERNAL

        # 404 errors aren't contextualized here because all 404s use the internal nginx redirect,
        # where the path will be 'unresolved' again when handling the 404 error
        # See: ServeError404Base
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
        except TranslationWithoutVersionError as exc:
            project = exc.project
            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = project.slug

            if unresolved_domain.is_from_external_domain:
                version_slug = unresolved_domain.external_version_slug
            else:
                version_slug = None
            # Redirect to the default version of the current translation.
            # This is `/en -> /en/latest/` or
            # `/projects/subproject/en/ -> /projects/subproject/en/latest/`.
            return self.system_redirect(
                request=request,
                final_project=project,
                version_slug=version_slug,
                filename="",
                is_external_version=unresolved_domain.is_from_external_domain,
            )
        except InvalidPathForVersionedProjectError as exc:
            project = exc.project
            if unresolved_domain.is_from_external_domain:
                version_slug = unresolved_domain.external_version_slug
            else:
                version_slug = None

            # TODO: find a better way to pass this to the middleware.
            request.path_project_slug = project.slug
            request.path_version_slug = version_slug

            # Support redirecting to the default version from
            # the root path and the custom path prefix.
            root_paths = ["/"]
            if project.custom_prefix:
                # We need to check custom path prefixes with and without the trailing slash,
                # e.g: /foo and /foo/.
                root_paths.append(project.custom_prefix)
                root_paths.append(project.custom_prefix.rstrip("/"))

            if exc.path in root_paths:
                # When the path is empty, the project didn't have an explicit version,
                # so we need to redirect to the default version.
                # This is `/ -> /en/latest/` or
                # `/projects/subproject/ -> /projects/subproject/en/latest/`.
                return self.system_redirect(
                    request=request,
                    final_project=project,
                    version_slug=version_slug,
                    filename="",
                    is_external_version=unresolved_domain.is_from_external_domain,
                )

            raise Http404

        project = unresolved.project
        version = unresolved.version
        filename = unresolved.filename

        # Inject the UnresolvedURL into the HttpRequest so we can access from the middleware.
        # We could resolve it again from the middleware, but we would duplicating DB queries.
        request.unresolved_url = unresolved

        # Check if the old language code format was used, and redirect to the new one.
        # NOTE: we may have some false positives here, for example for an URL like:
        # /pt-br/latest/pt_BR/index.html, but our protection for infinite redirects
        # will prevent a redirect loop.
        if (
            project.supports_translations
            and project.language in OLD_LANGUAGES_CODE_MAPPING
            and OLD_LANGUAGES_CODE_MAPPING[project.language] in path
        ):
            try:
                return self.system_redirect(
                    request=request,
                    final_project=project,
                    version_slug=version.slug,
                    filename=filename,
                    is_external_version=unresolved_domain.is_from_external_domain,
                )
            except InfiniteRedirectException:
                # A false positive was detected, continue with our normal serve.
                pass

        structlog.contextvars.bind_contextvars(
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

        structlog.contextvars.bind_contextvars(cache_response=self.cache_response)
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

        # Check for forced redirects on non-external domains only.
        if not unresolved_domain.is_from_external_domain:
            try:
                redirect_response = self.get_redirect_response(
                    request=request,
                    project=project,
                    language=project.language,
                    version_slug=version.slug,
                    filename=filename,
                    path=request.path,
                    forced_only=True,
                )
                if redirect_response:
                    return redirect_response
            except InfiniteRedirectException:
                # Continue with our normal serve.
                pass

        # Check user permissions and return an unauthed response if needed.
        if not self.allowed_user(request, version):
            return self.get_unauthed_response(request, project)

        return self._serve_docs(
            request=request,
            project=project,
            version=version,
            filename=filename,
        )


class ServeDocs(SettingsOverrideObject):
    _default_class = ServeDocsBase


class ServeError404Base(CDNCacheControlMixin, ServeRedirectMixin, ServeDocsMixin, View):
    """
    Proxito handler for 404 pages.

    This view is called by an internal nginx redirect when there is a 404.
    """

    def get(self, request, proxito_path):
        """
        Handler for 404 pages on subdomains.

        This does a couple of things:

        * Handles directory indexing for URLs that don't end in a slash
        * Check for user redirects
        * Record the broken link for analytics
        * Handles custom 404 serving

        For 404's, first search for a 404 page in the current version, then continues
        with the default version and finally, if none of them are found, the Read
        the Docs default page (Maze Found) is rendered by Django and served.
        """
        structlog.contextvars.bind_contextvars(proxito_path=proxito_path)
        log.debug("Executing 404 handler.")
        unresolved_domain = request.unresolved_domain
        # We force all storage calls to use the external versions storage,
        # since we are serving an external version.
        # The version that results from the unresolve_path() call already is
        # validated to use the correct manager, this is here to add defense in
        # depth against serving the wrong version.
        if unresolved_domain.is_from_external_domain:
            self.version_type = EXTERNAL

        project = None
        version = None
        # If we weren't able to resolve a filename,
        # then the path is the filename.
        filename = proxito_path
        lang_slug = None
        version_slug = None
        # Try to map the current path to a project/version/filename.
        # If that fails, we fill the variables with the information we have
        # available in the exceptions.

        contextualized_404_class = ContextualizedHttp404

        try:
            unresolved = unresolver.unresolve_path(
                unresolved_domain=unresolved_domain,
                path=proxito_path,
                append_indexhtml=False,
            )

            # Inject the UnresolvedURL into the HttpRequest so we can access from the middleware.
            # We could resolve it again from the middleware, but we would duplicating DB queries.
            request.unresolved_url = unresolved

            project = unresolved.project
            version = unresolved.version
            filename = unresolved.filename
            lang_slug = project.language
            version_slug = version.slug
            contextualized_404_class = ProjectFilenameHttp404
        except VersionNotFoundError as exc:
            project = exc.project
            lang_slug = project.language
            version_slug = exc.version_slug
            filename = exc.filename
            contextualized_404_class = ProjectVersionHttp404
        except TranslationNotFoundError as exc:
            project = exc.project
            lang_slug = exc.language
            version_slug = exc.version_slug
            filename = exc.filename
            contextualized_404_class = ProjectTranslationHttp404
        except TranslationWithoutVersionError as exc:
            project = exc.project
            lang_slug = exc.language
            # TODO: Use a contextualized 404
        except InvalidExternalVersionError as exc:
            project = exc.project
            # TODO: Use a contextualized 404
        except InvalidPathForVersionedProjectError as exc:
            project = exc.project
            filename = exc.path
            # TODO: Use a contextualized 404

        structlog.contextvars.bind_contextvars(
            project_slug=project.slug,
            version_slug=version_slug,
        )

        # TODO: find a better way to pass this to the middleware.
        request.path_project_slug = project.slug
        request.path_version_slug = version_slug

        # If we were able to resolve to a valid version, it means that the
        # current file doesn't exist. So we check if we can redirect to its
        # index file if it exists before doing anything else.
        # If the version isn't marked as built, we don't check for index files,
        # since the version doesn't have any files.
        # This is /en/latest/foo -> /en/latest/foo/index.html.
        if version and version.built:
            response = self._get_index_file_redirect(
                request=request,
                project=project,
                version=version,
                filename=filename,
                full_path=proxito_path,
            )
            if response:
                return response

        # Check and perform redirects on 404 handler for non-external domains only.
        # NOTE: This redirect check must be done after trying files like
        # ``index.html`` to emulate the behavior we had when
        # serving directly from NGINX without passing through Python.
        if not unresolved_domain.is_from_external_domain:
            try:
                redirect_response = self.get_redirect_response(
                    request=request,
                    project=project,
                    language=lang_slug,
                    version_slug=version_slug,
                    filename=filename,
                    path=proxito_path,
                )
                if redirect_response:
                    return redirect_response
            except InfiniteRedirectException:
                # ``get_redirect_response`` raises this when it's redirecting back to itself.
                # We can safely ignore it here because it's logged in ``canonical_redirect``,
                # and we don't want to issue infinite redirects.
                pass

        response = self._get_custom_404_page(
            request=request,
            project=project,
            version=version,
        )
        if response:
            return response

        # Don't use the custom 404 page, use our general contextualized 404 response
        # Several additional context variables can be added if the templates
        # or other error handling is developed (version, language, filename).
        raise contextualized_404_class(
            project=project,
            path_not_found=proxito_path,
        )

    def _get_custom_404_page(self, request, project, version=None):
        """
        Try to serve a custom 404 page from this project.

        If a version is given, try to serve the 404 page from that version first,
        if it doesn't exist, try to serve the 404 page from the default version.

        We check for a 404.html or 404/index.html file.

        We don't check for a custom 404 page in versions that aren't marked as built,
        since they don't have any files.

        If a 404 page is found, we return a response with the content of that file,
        `None` otherwise.
        """
        versions_404 = [version] if version and version.built else []
        if not version or version.slug != project.default_version:
            default_version = project.versions.filter(slug=project.default_version).first()
            if default_version and default_version.built:
                versions_404.append(default_version)

        if not versions_404:
            return None

        tryfiles = ["404.html", "404/index.html"]
        available_404_files = list(
            HTMLFile.objects.filter(version__in=versions_404, path__in=tryfiles).values_list(
                "version__slug", "path"
            )
        )
        if not available_404_files:
            return None

        for version_404 in versions_404:
            if not self.allowed_user(request, version_404):
                continue

            for tryfile in tryfiles:
                if (version_404.slug, tryfile) not in available_404_files:
                    continue

                storage_root_path = project.get_storage_path(
                    type_="html",
                    version_slug=version_404.slug,
                    include_file=False,
                    version_type=self.version_type,
                )
                storage_filename_path = build_media_storage.join(storage_root_path, tryfile)
                log.debug(
                    "Serving custom 404.html page.",
                    version_slug_404=version_404.slug,
                    storage_filename_path=storage_filename_path,
                )
                try:
                    content = build_media_storage.open(storage_filename_path).read()
                    return HttpResponse(content, status=404)
                except FileNotFoundError:
                    log.warning(
                        "File not found in storage. File out of sync with DB.",
                        file=storage_filename_path,
                    )
                    return None
        return None

    def _get_index_file_redirect(self, request, project, version, filename, full_path):
        """
        Check if a file is a directory and redirect to its index file.

        For example:

        - /en/latest/foo -> /en/latest/foo/index.html
        """
        # If the path ends with `/`, we already tried to serve
        # the `/index.html` file.
        if full_path.endswith("/"):
            return None

        tryfile = (filename.rstrip("/") + "/index.html").lstrip("/")
        if not HTMLFile.objects.filter(version=version, path=tryfile).exists():
            return None

        log.info("Redirecting to index file.", tryfile=tryfile)
        # Use urlparse so that we maintain GET args in our redirect
        parts = urlparse(full_path)
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


class ServeError404(SettingsOverrideObject):
    _default_class = ServeError404Base


class ServeRobotsTXTBase(CDNCacheControlMixin, CDNCacheTagsMixin, ServeDocsMixin, View):
    """Serve robots.txt from the domain's root."""

    # Always cache this view, since it's the same for all users.
    cache_response = True
    # Extra cache tag to invalidate only this view if needed.
    project_cache_tag = "robots.txt"

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
        if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import is_robotstxt_denied  # noqa

            if is_robotstxt_denied(project):
                return render(
                    request,
                    "robots.spam.txt",
                    content_type="text/plain",
                )

        # Use the ``robots.txt`` file from the default version configured
        version_slug = project.get_default_version()
        version = project.versions.get(slug=version_slug)

        no_serve_robots_txt = any(
            [
                # If the default version is private or,
                version.privacy_level == PRIVATE,
                # default version is not active or,
                not version.active,
                # default version is not built
                not version.built,
            ]
        )

        if no_serve_robots_txt:
            # ... we do return a 404
            raise Http404()

        structlog.contextvars.bind_contextvars(
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
            log.info("Serving custom robots.txt file.")
            return response
        except StorageFileNotFound:
            pass

        # Serve default robots.txt
        sitemap_url = "{scheme}://{domain}/sitemap.xml".format(
            scheme="https",
            domain=project.subdomain(),
        )
        context = {
            "sitemap_url": sitemap_url,
            "hidden_paths": self._get_hidden_paths(project),
        }
        return render(
            request,
            "robots.txt",
            context,
            content_type="text/plain",
        )

    def _get_hidden_paths(self, project):
        """Get the absolute paths of the public hidden versions of `project`."""
        hidden_versions = project.versions(manager=INTERNAL).public().filter(hidden=True)
        resolver = Resolver()
        hidden_paths = [
            resolver.resolve_path(project, version_slug=version.slug) for version in hidden_versions
        ]
        return hidden_paths

    def _get_project(self):
        # Method used by the CDNCacheTagsMixin class.
        return self.request.unresolved_domain.project

    def _get_version(self):
        # Method used by the CDNCacheTagsMixin class.
        # This view isn't explicitly mapped to a version,
        # but it can be when we serve a custom robots.txt file.
        # TODO: refactor how we set cache tags to avoid this.
        return None


class ServeRobotsTXT(SettingsOverrideObject):
    _default_class = ServeRobotsTXTBase


class ServeSitemapXMLBase(CDNCacheControlMixin, CDNCacheTagsMixin, View):
    """Serve sitemap.xml from the domain's root."""

    # Always cache this view, since it's the same for all users.
    cache_response = True
    # Extra cache tag to invalidate only this view if needed.
    project_cache_tag = "sitemap.xml"

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
            priorities = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            yield from itertools.chain(priorities, itertools.repeat(0.1))

        def hreflang_formatter(lang):
            """
            sitemap hreflang should follow correct format.

            Use hyphen instead of underscore in language and country value.
            ref: https://en.wikipedia.org/wiki/Hreflang#Common_Mistakes
            """
            if "_" in lang:
                return lang.replace("_", "-")
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
            changefreqs = ["weekly", "daily"]
            yield from itertools.chain(changefreqs, itertools.repeat("monthly"))

        project = request.unresolved_domain.project
        public_versions = project.versions(manager=INTERNAL).public(
            only_active=True,
            include_hidden=False,
        )
        if not public_versions.exists():
            raise Http404()

        sorted_versions = sort_version_aware(public_versions)

        # This is a hack to swap the latest version with
        # stable version to get the stable version first in the sitemap.
        # We want stable with priority=1 and changefreq='weekly' and
        # latest with priority=0.9 and changefreq='daily'
        # More details on this: https://github.com/rtfd/readthedocs.org/issues/5447
        if (
            len(sorted_versions) >= 2
            and sorted_versions[0].slug == LATEST
            and sorted_versions[1].slug == STABLE
        ):
            sorted_versions[0], sorted_versions[1] = (
                sorted_versions[1],
                sorted_versions[0],
            )

        versions = []
        for version, priority, changefreq in zip(
            sorted_versions,
            priorities_generator(),
            changefreqs_generator(),
        ):
            element = {
                "loc": version.get_subdomain_url(),
                "priority": priority,
                "changefreq": changefreq,
                "languages": [],
            }

            # Version can be enabled, but not ``built`` yet. We want to show the
            # link without a ``lastmod`` attribute
            last_build = version.builds.order_by("-date").first()
            if last_build:
                element["lastmod"] = last_build.date.isoformat()

            resolver = Resolver()
            if project.translations.exists():
                for translation in project.translations.all():
                    translated_version = (
                        translation.versions(manager=INTERNAL)
                        .public()
                        .filter(slug=version.slug)
                        .first()
                    )
                    if translated_version:
                        href = resolver.resolve_version(
                            project=translation,
                            version=translated_version,
                        )
                        element["languages"].append(
                            {
                                "hreflang": hreflang_formatter(translation.language),
                                "href": href,
                            }
                        )

                # Add itself also as protocol requires
                element["languages"].append(
                    {
                        "hreflang": project.language,
                        "href": element["loc"],
                    }
                )

            versions.append(element)

        context = {
            "versions": versions,
        }
        return render(
            request,
            "sitemap.xml",
            context,
            content_type="application/xml",
        )

    def _get_project(self):
        # Method used by the CDNCacheTagsMixin class.
        return self.request.unresolved_domain.project

    def _get_version(self):
        # Method used by the CDNCacheTagsMixin class.
        # This view isn't explicitly mapped to a version,
        # TODO: refactor how we set cache tags to avoid this.
        return None


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
