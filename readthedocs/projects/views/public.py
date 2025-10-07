"""Public project views."""

import hashlib
import mimetypes
import os

import structlog
from django.conf import settings
from django.contrib import messages
from django.db.models import prefetch_related_objects
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_bytes
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView
from django.views.generic import ListView
from taggit.models import Tag

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.core.filters import FilterContextMixin
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.permissions import AdminPermission
from readthedocs.core.resolver import Resolver
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.notifications.models import Notification
from readthedocs.projects.filters import ProjectVersionListFilterSet
from readthedocs.projects.models import Project
from readthedocs.projects.views.mixins import ProjectRelationListMixin
from readthedocs.proxito.views.mixins import ServeDocsMixin

from ..constants import PRIVATE
from .base import ProjectOnboardMixin
from .base import ProjectSpamMixin


log = structlog.get_logger(__name__)
search_log = structlog.get_logger(__name__ + ".search")
mimetypes.add_type("application/epub+zip", ".epub")


class ProjectTagIndex(ListView):
    """List view of public :py:class:`Project` instances."""

    model = Project

    def get_queryset(self):
        queryset = Project.objects.public(self.request.user)

        # Filters out projects from banned users
        # This is disabled for performance reasons
        # https://github.com/readthedocs/readthedocs.org/pull/7671
        # queryset = queryset.exclude(users__profile__banned=True)

        self.tag = get_object_or_404(Tag, slug=self.kwargs.get("tag"))
        queryset = queryset.filter(tags__slug__in=[self.tag.slug])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context


def project_redirect(request, invalid_project_slug):
    """
    Redirect project slugs that have underscores (``_``).

    Slugs with underscores are no longer allowed.
    Underscores are replaced by ``-`` and then redirected to that URL.
    """
    new_project_slug = invalid_project_slug.replace("_", "-")
    new_path = request.path.replace(invalid_project_slug, new_project_slug)
    return redirect(
        "{}?{}".format(
            new_path,
            request.GET.urlencode(),
        )
    )


class ProjectDetailViewBase(
    FilterContextMixin,
    ProjectSpamMixin,
    ProjectRelationListMixin,
    ProjectOnboardMixin,
    DetailView,
):
    """Display project onboard steps."""

    model = Project
    slug_url_kwarg = "project_slug"

    filterset_class = ProjectVersionListFilterSet

    def _get_versions(self, project):
        return project.versions(manager=INTERNAL).public(
            user=self.request.user,
        )

    def get_queryset(self):
        return Project.objects.public(self.request.user)

    def get_project(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.get_project()

        # Get filtered and sorted versions
        versions = self._get_versions(project)
        context["filter"] = self.get_filterset(
            queryset=versions,
            project=project,
        )
        versions = self.get_filtered_queryset()
        context["versions"] = versions

        protocol = "http"
        if self.request.is_secure():
            protocol = "https"

        default_version_slug = project.get_default_version()
        default_version = project.versions.get(slug=default_version_slug)

        context["badge_url"] = ProjectBadgeView.get_badge_url(
            project.slug,
            default_version_slug,
            protocol=protocol,
        )
        context["site_url"] = "{url}?badge={version}".format(
            url=Resolver().resolve_version(project, version=default_version),
            version=default_version_slug,
        )

        context["is_project_admin"] = AdminPermission.is_admin(
            self.request.user,
            project,
        )
        context["notifications"] = Notification.objects.for_user(
            self.request.user,
            resource=project,
        )

        return context


class ProjectDetailView(SettingsOverrideObject):
    _default_class = ProjectDetailViewBase


class ProjectBadgeView(View):
    """
    Return a sweet badge for the project.

    Query parameters:

    * ``version`` the version for the project (latest [default], stable, etc.)
    * ``style`` the style of the badge (flat [default], plastic, etc.)
    * ``token`` a project-specific token needed to access private versions
    """

    http_method_names = ["get", "head", "options"]
    STATUS_UNKNOWN = "unknown"
    STATUS_PASSING = "passing"
    STATUS_FAILING = "failing"
    STATUSES = (STATUS_FAILING, STATUS_PASSING, STATUS_UNKNOWN)

    def get(self, request, project_slug, *args, **kwargs):
        status = self.STATUS_UNKNOWN
        token = request.GET.get("token")
        version_slug = request.GET.get("version", LATEST)
        version = None

        if token:
            version_to_check = Version.objects.filter(
                project__slug=project_slug,
                slug=version_slug,
            ).first()
            if version_to_check and self.verify_project_token(token, project_slug):
                version = version_to_check
        else:
            version = (
                Version.objects.public(request.user)
                .filter(
                    project__slug=project_slug,
                    slug=version_slug,
                )
                .first()
            )

        if version:
            last_build = (
                version.builds.filter(type="html", state=BUILD_STATE_FINISHED)
                .order_by("-date")
                .first()
            )
            if last_build:
                if last_build.success:
                    status = self.STATUS_PASSING
                else:
                    status = self.STATUS_FAILING

        return self.serve_badge(request, status)

    def get_style(self, request):
        style = request.GET.get("style", "flat")
        if style not in (
            "flat",
            "plastic",
            "flat-square",
            "for-the-badge",
            "social",
        ):
            style = "flat"

        return style

    def serve_badge(self, request, status):
        style = self.get_style(request)
        if status not in self.STATUSES:
            status = self.STATUS_UNKNOWN

        badge_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "static",
            "projects",
            "badges",
            f"{status}-{style}.svg",
        )

        try:
            # pylint: disable=unspecified-encoding
            with open(badge_path) as fd:
                return HttpResponse(
                    fd.read(),
                    content_type="image/svg+xml",
                )
        except (IOError, OSError):
            log.exception(
                "Failed to read local filesystem while serving a docs badge",
            )
            return HttpResponse(status=503)

    @classmethod
    def get_badge_url(cls, project_slug, version_slug, protocol="https"):
        url = "{}://{}{}?version={}".format(
            protocol,
            settings.PRODUCTION_DOMAIN,
            reverse("project_badge", args=[project_slug]),
            version_slug,
        )

        # Append a token for private versions
        privacy_level = (
            Version.objects.filter(
                project__slug=project_slug,
                slug=version_slug,
            )
            .values_list("privacy_level", flat=True)
            .first()
        )
        if privacy_level == PRIVATE:
            token = cls.get_project_token(project_slug)
            url += f"&token={token}"

        return url

    @classmethod
    def get_project_token(cls, project_slug):
        salt = b"readthedocs.projects.views.public.ProjectBadgeView"
        hash_id = hashlib.sha256()
        hash_id.update(force_bytes(settings.SECRET_KEY))
        hash_id.update(salt)
        hash_id.update(force_bytes(project_slug))
        return hash_id.hexdigest()

    @classmethod
    def verify_project_token(cls, token, project_slug):
        expected_token = cls.get_project_token(project_slug)
        return constant_time_compare(token, expected_token)


project_badge = never_cache(ProjectBadgeView.as_view())


class ProjectDownloadMediaBase(CDNCacheControlMixin, CDNCacheTagsMixin, ServeDocsMixin, View):
    # Use new-style URLs (same domain as docs) or old-style URLs (dashboard URL)
    same_domain_url = False

    def get(
        self,
        request,
        project_slug=None,
        type_=None,
        version_slug=None,
        lang_slug=None,
        subproject_slug=None,
    ):
        """
        Download a specific piece of media.

        Perform an auth check if serving in private mode.

        This view is used to download a file using old-style URLs (download from
        the dashboard) and new-style URLs (download from the same domain as
        docs). Basically, the parameters received by the GET view are different
        (``project_slug`` does not come in the new-style URLs, for example) and
        we need to take it from the request. Once we get the final ``version``
        to be served, everything is the same for both paths.

        .. warning:: This is linked directly from the HTML pages.
                     It should only care about the Version permissions,
                     not the actual Project permissions.
        """
        if self.same_domain_url:
            unresolved_domain = request.unresolved_domain
            is_external = request.unresolved_domain.is_from_external_domain
            manager = EXTERNAL if is_external else INTERNAL

            # Additional protection to force all storage calls
            # to use the external or internal versions storage.
            # TODO: We already force the manager to match the type,
            # so we could probably just remove this.
            self.version_type = manager

            # It uses the request to get the ``project``.
            # The rest of arguments come from the URL.
            project = unresolved_domain.project

            # Use the project from the domain, or use the subproject slug.
            if subproject_slug:
                project = get_object_or_404(project.subprojects, alias=subproject_slug).child

            # Redirect old language codes with underscores to new ones with dashes and lowercase.
            normalized_language_code = lang_slug.lower().replace("_", "-")
            if normalized_language_code != lang_slug:
                if project.language != normalized_language_code:
                    project = get_object_or_404(
                        project.translations, language=normalized_language_code
                    )
                return HttpResponseRedirect(
                    project.get_production_media_url(type_, version_slug=version_slug)
                )

            if project.language != lang_slug:
                project = get_object_or_404(project.translations, language=lang_slug)

            if is_external and unresolved_domain.external_version_slug != version_slug:
                raise Http404

            version = get_object_or_404(
                project.versions(manager=manager),
                slug=version_slug,
            )

            if not self.allowed_user(request, version):
                return self.get_unauthed_response(request, project)

            # All public versions can be cached.
            self.cache_response = version.is_public
        else:
            # All the arguments come from the URL.
            version = get_object_or_404(
                Version.internal.public(user=request.user),
                project__slug=project_slug,
                slug=version_slug,
            )

        # TODO don't do this, it's a leftover of trying to use CDNCacheTagsMixin
        # without class level variables. See proxito.views.serve for
        # other instances of this pattern to update.
        # See: https://github.com/readthedocs/readthedocs.org/pull/12495
        self.project = version.project
        self.version = version

        return self._serve_dowload(
            request=request,
            project=version.project,
            version=version,
            type_=type_,
        )

    def _get_project(self):
        """Hack for CDNCacheTagsMixin, get project set in `get()`."""
        return self.project

    def _get_version(self):
        """Hack for CDNCacheTagsMixin, get version set in `get()`."""
        return self.version


class ProjectDownloadMedia(SettingsOverrideObject):
    _default_class = ProjectDownloadMediaBase


def project_versions(request, project_slug):
    """
    Project version list view.

    Shows the available versions and lets the user choose which ones to build.
    """
    max_inactive_versions = 100

    project = get_object_or_404(
        Project.objects.public(request.user),
        slug=project_slug,
    )

    versions = project.versions(manager=INTERNAL).public(
        user=request.user,
        only_active=False,
    )
    active_versions = versions.filter(active=True)

    # Limit inactive versions in case a project has a large number of branches or tags
    # Filter inactive versions based on the query string
    inactive_versions = versions.filter(active=False)
    version_filter = request.GET.get("version_filter", "")
    if version_filter:
        inactive_versions = inactive_versions.filter(verbose_name__icontains=version_filter)
    total_inactive_versions_count = inactive_versions.count()
    inactive_versions = inactive_versions[:max_inactive_versions]

    # If there's a wiped query string, check the string against the versions
    # list and display a success message. Deleting directories doesn't know how
    # to fail.  :)
    wiped = request.GET.get("wipe", "")
    wiped_version = versions.filter(slug=wiped)
    if wiped and wiped_version.exists():
        messages.success(request, "Version wiped: " + wiped)

    # Optimize project permission checks
    prefetch_related_objects([project], "users")

    return render(
        request,
        "projects/project_version_list.html",
        {
            "inactive_versions": inactive_versions,
            "active_versions": active_versions,
            "project": project,
            "is_project_admin": AdminPermission.is_admin(request.user, project),
            "max_inactive_versions": max_inactive_versions,
            "total_inactive_versions_count": total_inactive_versions_count,
        },
    )
