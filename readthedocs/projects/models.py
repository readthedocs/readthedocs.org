"""Project models."""

import fnmatch
import hashlib
import hmac
import os
import re
from shlex import quote
from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField
from django_extensions.db.fields import ModificationDateTimeField
from django_extensions.db.models import TimeStampedModel
from taggit.managers import TaggableManager

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import STABLE_VERBOSE_NAME
from readthedocs.core.history import ExtraHistoricalRecords
from readthedocs.core.resolver import Resolver
from readthedocs.core.utils import extract_valid_attributes_for_model
from readthedocs.core.utils import slugify
from readthedocs.core.utils.url import unsafe_join_url_path
from readthedocs.domains.querysets import DomainQueryset
from readthedocs.domains.validators import check_domains_limit
from readthedocs.notifications.models import Notification as NewNotification
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.managers import HTMLFileManager
from readthedocs.projects.querysets import ChildRelatedProjectQuerySet
from readthedocs.projects.querysets import FeatureQuerySet
from readthedocs.projects.querysets import ProjectQuerySet
from readthedocs.projects.querysets import RelatedProjectQuerySet
from readthedocs.projects.validators import validate_build_config_file
from readthedocs.projects.validators import validate_custom_prefix
from readthedocs.projects.validators import validate_custom_subproject_prefix
from readthedocs.projects.validators import validate_domain_name
from readthedocs.projects.validators import validate_environment_variable_size
from readthedocs.projects.validators import validate_no_ip
from readthedocs.projects.validators import validate_repository_url
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.search.parsers import GenericParser
from readthedocs.storage import build_media_storage
from readthedocs.vcs_support.backends import backend_cls

from .constants import ADDONS_FLYOUT_POSITION_CHOICES
from .constants import ADDONS_FLYOUT_SORTING_CHOICES
from .constants import ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE
from .constants import DOWNLOADABLE_MEDIA_TYPES
from .constants import MEDIA_TYPES
from .constants import MULTIPLE_VERSIONS_WITH_TRANSLATIONS
from .constants import MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS
from .constants import PUBLIC


log = structlog.get_logger(__name__)


def default_privacy_level():
    """Wrapper around the setting, so the level is dynamically included in the migration."""
    return settings.DEFAULT_PRIVACY_LEVEL


class ProjectRelationship(models.Model):
    """
    Project to project relationship.

    This is used for subprojects.

    Terminology: We should say main project and subproject.
    Saying "child" and "parent" only has internal, technical value.
    """

    parent = models.ForeignKey(
        "projects.Project",
        verbose_name=_("Main project"),
        related_name="subprojects",
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        "projects.Project",
        verbose_name=_("Subproject"),
        related_name="superprojects",
        on_delete=models.CASCADE,
    )
    alias = models.SlugField(
        _("Alias"),
        max_length=255,
        null=True,
        blank=True,
        db_index=False,
    )

    objects = ChildRelatedProjectQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self.alias:
            self.alias = self.child.slug
        super().save(*args, **kwargs)

    # HACK
    def get_absolute_url(self):
        return Resolver().resolve_version(project=self.child)

    @cached_property
    def subproject_prefix(self):
        """
        Returns the path prefix of the subproject.

        This normally is ``/projects/<subproject-alias>/``,
        but if the project has a custom subproject prefix,
        that will be used.
        """
        prefix = self.parent.custom_subproject_prefix or "/projects/"
        return unsafe_join_url_path(prefix, self.alias, "/")


class AddonsConfig(TimeStampedModel):
    """
    Addons project configuration.

    Store all the configuration for each of the addons.
    Everything is enabled by default.
    """

    # Model history
    history = ExtraHistoricalRecords()

    project = models.OneToOneField(
        "Project",
        related_name="addons",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    enabled = models.BooleanField(
        default=True,
        help_text="Enable/Disable all the addons on this project",
    )

    options_root_selector = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        help_text="CSS selector for the main content of the page. Leave it blank for auto-detect.",
    )

    # Whether or not load addons library when the requested page is embedded (e.g. inside an iframe)
    # https://github.com/readthedocs/addons/pull/415
    options_load_when_embedded = models.BooleanField(default=False)

    options_base_version = models.ForeignKey(
        "builds.Version",
        verbose_name=_("Base version to compare against (eg. DocDiff, File Tree Diff)"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Analytics

    # NOTE: we keep analytics disabled by default to save resources.
    # Most projects won't be taking a look at these numbers.
    analytics_enabled = models.BooleanField(default=False)

    # Docdiff
    doc_diff_enabled = models.BooleanField(default=True)
    doc_diff_show_additions = models.BooleanField(default=True)
    doc_diff_show_deletions = models.BooleanField(default=True)

    # EthicalAds
    ethicalads_enabled = models.BooleanField(default=True)

    # File Tree Diff
    filetreediff_enabled = models.BooleanField(default=True)
    filetreediff_ignored_files = models.JSONField(
        help_text=_("List of ignored files. One per line."),
        null=True,
        blank=True,
    )

    # Flyout
    flyout_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
    )
    flyout_sorting = models.CharField(
        verbose_name=_("Sorting of versions"),
        choices=ADDONS_FLYOUT_SORTING_CHOICES,
        default=ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE,
        max_length=64,
    )
    flyout_sorting_custom_pattern = models.CharField(
        max_length=32,
        default=None,
        null=True,
        blank=True,
        verbose_name=_("Custom version sorting pattern"),
        help_text="Sorting pattern supported by BumpVer "
        '(<a href="https://github.com/mbarkhau/bumpver#pattern-examples">See examples</a>)',
    )
    flyout_sorting_latest_stable_at_beginning = models.BooleanField(
        verbose_name=_("Show <code>latest</code> and <code>stable</code> at the beginning"),
        default=True,
    )

    flyout_position = models.CharField(
        choices=ADDONS_FLYOUT_POSITION_CHOICES,
        max_length=64,
        default=None,  # ``None`` means use the default (theme override if present or Read the Docs default)
        null=True,
        blank=True,
        verbose_name=_("Position"),
    )

    # Hotkeys
    hotkeys_enabled = models.BooleanField(default=True)

    # Search
    search_enabled = models.BooleanField(default=True)
    search_default_filter = models.CharField(null=True, blank=True, max_length=128)

    # User JavaScript File
    customscript_enabled = models.BooleanField(default=False)

    # This is a user-defined file that will be injected at serve time by our
    # Cloudflare Worker if defined
    customscript_src = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text="URL to a JavaScript file to inject at serve time",
    )

    # Notifications
    notifications_enabled = models.BooleanField(default=True)
    notifications_show_on_latest = models.BooleanField(default=True)
    notifications_show_on_non_stable = models.BooleanField(default=True)
    notifications_show_on_external = models.BooleanField(default=True)

    # Link Previews
    linkpreviews_enabled = models.BooleanField(default=False)
    linkpreviews_selector = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        help_text="CSS selector to select links you want enabled for link previews. Leave it blank for auto-detect all links in your main page content.",
    )


class AddonSearchFilter(TimeStampedModel):
    """
    Addon search user defined filter.

    Specific filter defined by the user to show on the search modal.
    """

    addons = models.ForeignKey("AddonsConfig", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    syntaxt = models.CharField(max_length=128)


class Project(models.Model):
    """Project model."""

    # Auto fields
    pub_date = models.DateTimeField(_("Publication date"), auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(_("Modified date"), auto_now=True, db_index=True)

    # Generally from conf.py
    users = models.ManyToManyField(
        User,
        verbose_name=_("User"),
        related_name="projects",
    )
    # A DNS label can contain up to 63 characters.
    name = models.CharField(_("Name"), max_length=63)
    slug = models.SlugField(_("Slug"), max_length=63, unique=True)
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Short description of this project"),
    )

    # Example:
    # [
    #     "git clone --no-checkout --no-tag --filter=blob:none --depth 1 $READTHEDOCS_GIT_CLONE_URL .",
    #     "git checkout $READTHEDOCS_GIT_IDENTIFIER"
    # ]
    git_checkout_command = models.JSONField(
        _("Custom command to execute before Git checkout"),
        null=True,
        blank=True,
    )

    repo = models.CharField(
        _("Repository URL"),
        max_length=255,
        validators=[validate_repository_url],
        help_text=_("Git repository URL"),
    )

    # NOTE: this field is going to be completely removed soon.
    # We only accept Git for new repositories
    repo_type = models.CharField(
        _("Repository type"),
        max_length=10,
        choices=constants.REPO_CHOICES,
        default="git",
    )
    project_url = models.URLField(
        _("Project homepage"),
        blank=True,
        help_text=_("The project's homepage"),
    )
    canonical_url = models.URLField(
        _("Canonical URL"),
        blank=True,
        help_text=_("URL that documentation is expected to serve from"),
    )
    versioning_scheme = models.CharField(
        _("URL versioning scheme"),
        max_length=120,
        default=constants.MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
        choices=constants.VERSIONING_SCHEME_CHOICES,
        # TODO: remove after migration
        null=True,
        help_text=_(
            "This affects URL your documentation is served from, "
            "and if it supports translations or versions. "
            "Changing the versioning scheme will break your current URLs, "
            "so you might need to create a redirect."
        ),
    )
    # TODO: this field is deprecated, use `versioning_scheme` instead.
    single_version = models.BooleanField(
        _("Single version"),
        default=False,
        help_text=_(
            "A single version site has no translations and only your "
            '"latest" version, served at the root of the domain. Use '
            "this with caution, only turn it on if you will <b>never</b> "
            "have multiple versions of your docs.",
        ),
    )
    default_version = models.CharField(
        _("Default version"),
        max_length=255,
        default=LATEST,
        help_text=_("The version of your project that / redirects to"),
    )
    # In default_branch, ``None`` means the backend will use the default branch
    # cloned for each backend.
    default_branch = models.CharField(
        _("Default branch"),
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'What branch "latest" points to. Leave empty to use the default value for your VCS.',
        ),
    )
    custom_prefix = models.CharField(
        _("Custom path prefix"),
        max_length=255,
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "A custom path prefix used when serving documentation from this project. "
            "By default we serve documentation at the root (/) of a domain."
        ),
    )
    custom_subproject_prefix = models.CharField(
        _("Custom subproject path prefix"),
        max_length=255,
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "A custom path prefix used when evaluating the root of a subproject. "
            "By default we serve documentation from subprojects under the `/projects/` prefix."
        ),
    )

    # External versions
    external_builds_enabled = models.BooleanField(
        _("Build pull requests for this project"),
        default=False,
        help_text=_(
            'More information in <a href="https://docs.readthedocs.io/page/guides/autobuild-docs-for-pull-requests.html">our docs</a>.'  # noqa
        ),
    )
    external_builds_privacy_level = models.CharField(
        _("Privacy level of Pull Requests"),
        max_length=20,
        # TODO: remove after migration
        null=True,
        choices=constants.PRIVACY_CHOICES,
        default=default_privacy_level,
        help_text=_(
            "Should builds from pull requests be public? <strong>If your repository is public, don't set this to private</strong>."
        ),
    )
    show_build_overview_in_comment = models.BooleanField(
        _("Show build overview in a comment"),
        db_default=False,
        help_text=_(
            "Show an overview of the build and files changed in a comment when a pull request is built."
        ),
    )

    # Project features
    cdn_enabled = models.BooleanField(_("CDN Enabled"), default=False)
    analytics_code = models.CharField(
        _("Analytics code"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_(
            "Google Analytics Tracking ID "
            "(ex. <code>UA-22345342-1</code>). "
            "This may slow down your page loads.",
        ),
    )
    analytics_disabled = models.BooleanField(
        _("Disable Analytics"),
        default=False,
        null=True,
        help_text=_(
            "Disable Google Analytics completely for this project "
            "(requires rebuilding documentation)",
        ),
    )
    container_image = models.CharField(
        _("Alternative container image"),
        max_length=64,
        null=True,
        blank=True,
    )
    container_mem_limit = models.CharField(
        _("Container memory limit"),
        max_length=10,
        null=True,
        blank=True,
        help_text=_(
            "Memory limit in Docker format -- example: <code>512m</code> or <code>1g</code>",
        ),
    )
    container_time_limit = models.IntegerField(
        _("Container time limit in seconds"),
        null=True,
        blank=True,
    )
    build_queue = models.CharField(
        _("Alternate build queue id"),
        max_length=32,
        null=True,
        blank=True,
    )
    max_concurrent_builds = models.IntegerField(
        _("Maximum concurrent builds allowed for this project"),
        null=True,
        blank=True,
    )
    allow_promos = models.BooleanField(
        _("Allow paid advertising"),
        default=True,
        help_text=_("If unchecked, users will still see community ads."),
    )
    ad_free = models.BooleanField(
        _("Ad-free"),
        default=False,
        help_text="If checked, do not show advertising for this project",
    )
    is_spam = models.BooleanField(
        _("Is spam?"),
        default=None,
        null=True,
        help_text=_("Manually marked as (not) spam"),
    )
    show_version_warning = models.BooleanField(
        _("Show version warning"),
        default=False,
        help_text=_("Show warning banner in non-stable nor latest versions."),
    )

    readthedocs_yaml_path = models.CharField(
        _("Path for .readthedocs.yaml"),
        max_length=1024,
        default=None,
        blank=True,
        null=True,
        help_text=_(
            "<strong>Warning: experimental feature</strong>. "
            "Custom path from repository top-level to your <code>.readthedocs.yaml</code>, "
            "ex. <code>subpath/docs/.readthedocs.yaml</code>. "
            "Leave blank for default value: <code>.readthedocs.yaml</code>.",
        ),
        validators=[validate_build_config_file],
    )

    featured = models.BooleanField(_("Featured"), default=False)

    skip = models.BooleanField(_("Skip (disable) building this project"), default=False)

    # null=True can be removed in a later migration
    # be careful if adding new queries on this, .filter(delisted=False) does not work
    # but .exclude(delisted=True) does!
    delisted = models.BooleanField(
        null=True,
        default=False,
        verbose_name=_("Delisted"),
        help_text=_(
            "Delisting a project removes it from Read the Docs search indexing and asks external "
            "search engines to remove it via robots.txt"
        ),
    )

    search_indexing_enabled = models.BooleanField(
        _("Enable search indexing"),
        default=True,
        db_default=True,
        help_text=_("Enable/disable search indexing for this project"),
    )

    privacy_level = models.CharField(
        _("Privacy Level"),
        max_length=20,
        choices=constants.PRIVACY_CHOICES,
        default=settings.DEFAULT_PRIVACY_LEVEL,
        help_text=_(
            "Should the project dashboard be public?",
        ),
    )

    # Subprojects
    related_projects = models.ManyToManyField(
        "self",
        verbose_name=_("Related projects"),
        blank=True,
        symmetrical=False,
        through=ProjectRelationship,
    )

    # Language bits
    language = models.CharField(
        _("Language"),
        max_length=20,
        default="en",
        help_text=_(
            "The language the project "
            "documentation is rendered in. "
            "Note: this affects your project's URL.",
        ),
        choices=constants.LANGUAGES,
    )

    programming_language = models.CharField(
        _("Programming Language"),
        max_length=20,
        default="words",
        help_text=_(
            "The primary programming language the project is written in.",
        ),
        choices=constants.PROGRAMMING_LANGUAGES,
        blank=True,
    )
    # A subproject pointed at its main language, so it can be tracked
    main_language_project = models.ForeignKey(
        "self",
        related_name="translations",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    has_valid_webhook = models.BooleanField(
        default=False,
        help_text=_("This project has been built with a webhook"),
    )
    has_valid_clone = models.BooleanField(
        default=False,
        help_text=_("This project has been successfully cloned"),
    )

    tags = TaggableManager(blank=True, ordering=["name"])
    history = ExtraHistoricalRecords(
        no_db_index=["repo", "slug", "remote_repository_id", "main_language_project_id"]
    )
    objects = ProjectQuerySet.as_manager()

    remote_repository = models.ForeignKey(
        "oauth.RemoteRepository",
        verbose_name=_("Connected repository"),
        help_text=_("Repository connected to this project"),
        on_delete=models.SET_NULL,
        related_name="projects",
        null=True,
        blank=True,
    )

    notifications = GenericRelation(
        NewNotification,
        related_query_name="project",
        content_type_field="attached_to_content_type",
        object_id_field="attached_to_id",
    )

    # TODO: remove field ``documentation_type`` when possible.
    # This field is not used anymore in the application.
    # However, the APIv3 project details endpoint returns it,
    # and there are some tests and similars that depend on it still.
    documentation_type = models.CharField(
        _("Documentation type"),
        max_length=20,
        choices=constants.DOCUMENTATION_CHOICES,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'Type of documentation you are building. <a href="'
            "http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html."
            'DirectoryHTMLBuilder">More info on sphinx builders</a>.',
        ),
    )

    # Keep track if the SSH key has write access or not (RTD Business),
    # so we can take further actions if needed.
    has_ssh_key_with_write_access = models.BooleanField(
        help_text=_("Project has an SSH key with write access"),
        default=False,
        null=True,
    )

    # Denormalized fields
    latest_build = models.OneToOneField(
        "builds.Build",
        verbose_name=_("Latest build"),
        # No reverse relation needed.
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("slug",)
        verbose_name = _("project")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Subdomains can't have underscores in them.
            self.slug = slugify(self.name)
            if not self.slug:
                raise Exception(  # pylint: disable=broad-exception-raised
                    _("Model must have slug")
                )

        # If the project is linked to a remote repository,
        # and the repository is public, we force the privacy level of
        # pull requests previews to be public, see GHSA-pw32-ffxw-68rh.
        if self.remote_repository and not self.remote_repository.private:
            self.external_builds_privacy_level = PUBLIC

        # If the project is linked to a remote repository,
        # make sure to use the clone URL from the repository.
        dont_sync = self.pk and self.has_feature(Feature.DONT_SYNC_WITH_REMOTE_REPO)
        if self.remote_repository and not dont_sync:
            self.repo = self.remote_repository.clone_url

        super().save(*args, **kwargs)
        self.update_latest_version()

    def delete(self, *args, **kwargs):
        from readthedocs.projects.tasks.utils import clean_project_resources

        # NOTE: We use _raw_delete to avoid Django fetching all objects
        # before the deletion. Be careful when using _raw_delete, signals
        # won't be sent, and can cause integrity problems if the model
        # has relations with other models.
        qs = self.page_views.all()
        qs._raw_delete(qs.db)
        qs = self.search_queries.all()
        qs._raw_delete(qs.db)

        # Remove extra resources
        clean_project_resources(self)

        super().delete(*args, **kwargs)

    def clean(self):
        if self.custom_prefix:
            self.custom_prefix = validate_custom_prefix(self, self.custom_prefix)

        if self.custom_subproject_prefix:
            self.custom_subproject_prefix = validate_custom_subproject_prefix(
                self, self.custom_subproject_prefix
            )

    def get_absolute_url(self):
        return reverse("projects_detail", args=[self.slug])

    def get_docs_url(
        self,
        version_slug=None,
        lang_slug=None,
        external=False,
        resolver=None,
    ):
        """
        Return a URL for the docs.

        ``external`` defaults False because we only link external versions in very specific places.
        ``resolver`` is used to "share a resolver" between the same request.
        """
        resolver = resolver or Resolver()
        return resolver.resolve(
            project=self,
            version_slug=version_slug,
            language=lang_slug,
            external=external,
        )

    def get_builds_url(self):
        return reverse(
            "builds_project_list",
            kwargs={
                "project_slug": self.slug,
            },
        )

    def get_storage_paths(self):
        """
        Get the paths of all artifacts used by the project.

        :return: the path to an item in storage
                 (can be used with ``storage.url`` to get the URL).
        """
        storage_paths = [f"{type_}/{self.slug}" for type_ in MEDIA_TYPES]
        return storage_paths

    def get_storage_path(self, type_, version_slug=LATEST, include_file=True, version_type=None):
        """
        Get a path to a build artifact for use with Django's storage system.

        :param type_: Media content type, ie - 'pdf', 'htmlzip'
        :param version_slug: Project version slug for lookup
        :param include_file: Include file name in return
        :param version_type: Project version type
        :return: the path to an item in storage
            (can be used with ``storage.url`` to get the URL)
        """
        if type_ not in MEDIA_TYPES:
            raise ValueError("Invalid content type.")

        if include_file and type_ not in DOWNLOADABLE_MEDIA_TYPES:
            raise ValueError("Invalid content type for downloadable file.")

        type_dir = type_
        # Add `external/` prefix for external versions
        if version_type == EXTERNAL:
            type_dir = f"{EXTERNAL}/{type_}"

        # Version slug may come from an unstrusted input,
        # so we use join to avoid any path traversal.
        # All other values are already validated.
        folder_path = build_media_storage.join(f"{type_dir}/{self.slug}", version_slug)

        if include_file:
            extension = type_.replace("htmlzip", "zip")
            return "{}/{}.{}".format(
                folder_path,
                self.slug,
                extension,
            )
        return folder_path

    def get_production_media_url(self, type_, version_slug, resolver=None):
        """Get the URL for downloading a specific media file."""
        # Use project domain for full path --same domain as docs
        # (project-slug.{PUBLIC_DOMAIN} or docs.project.com)
        domain = self.subdomain(resolver=resolver)

        # NOTE: we can't use ``reverse('project_download_media')`` here
        # because this URL only exists in El Proxito and this method is
        # accessed from Web instance

        main_project = self.main_language_project or self
        if main_project.is_subproject:
            # docs.example.com/_/downloads/<alias>/<lang>/<ver>/pdf/
            path = f"//{domain}/{self.proxied_api_url}downloads/{main_project.alias}/{self.language}/{version_slug}/{type_}/"  # noqa
        else:
            # docs.example.com/_/downloads/<lang>/<ver>/pdf/
            path = f"//{domain}/{self.proxied_api_url}downloads/{self.language}/{version_slug}/{type_}/"  # noqa

        return path

    @property
    def proxied_api_host(self):
        """
        Used for the proxied_api_host in javascript.

        This needs to start with a slash at the root of the domain,
        and end without a slash
        """
        custom_prefix = self.proxied_api_prefix
        if custom_prefix:
            return unsafe_join_url_path(custom_prefix, "/_")
        return "/_"

    @property
    def proxied_api_url(self):
        """
        Like the api_host but for use as a URL prefix.

        It can't start with a /, but has to end with one.
        """
        return self.proxied_api_host.strip("/") + "/"

    @property
    def proxied_static_path(self):
        """Path for static files hosted on the user's doc domain."""
        return f"{self.proxied_api_host}/static/"

    @property
    def proxied_api_prefix(self):
        """
        Get the path prefix for proxied API paths (``/_/``).

        Returns `None` if the project doesn't have a custom prefix.
        """
        # When using a custom prefix, we can only handle serving
        # docs pages under the prefix, not special paths like `/_/`.
        # Projects using the old implementation, need to proxy `/_/`
        # paths as is, this is, without the prefix, while those projects
        # migrate to the new implementation, we will prefix special paths
        # when generating links, these paths will be manually un-prefixed in nginx.
        if self.custom_prefix and self.has_feature(Feature.USE_PROXIED_APIS_WITH_PREFIX):
            return self.custom_prefix
        return None

    @cached_property
    def subproject_prefix(self):
        """
        Returns the path prefix of a subproject.

        This normally is ``/projects/<subproject-alias>/``,
        but if the project has a custom subproject prefix,
        that will be used.

        Returns `None` if the project isn't a subproject.
        """
        parent_relationship = self.parent_relationship
        if not parent_relationship:
            return None
        return parent_relationship.subproject_prefix

    @cached_property
    def is_subproject(self):
        """Return whether or not this project is a subproject."""
        return self.superprojects.exists()

    @cached_property
    def superproject(self):
        relationship = self.parent_relationship
        if relationship:
            return relationship.parent
        return None

    @property
    def alias(self):
        """Return the alias (as subproject) if it's a subproject."""  # noqa
        if self.is_subproject:
            return self.superprojects.first().alias

    @property
    def is_single_version(self):
        """
        Return whether or not this project is a single version without translations.

        Kept for backwards compatibility while we migrate the old field to the new one.
        """
        if self.single_version:
            return True
        return self.versioning_scheme == constants.SINGLE_VERSION_WITHOUT_TRANSLATIONS

    @property
    def supports_multiple_versions(self):
        """Return whether or not this project supports multiple versions."""
        return self.versioning_scheme in [
            MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
            MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
        ]

    @property
    def supports_translations(self):
        """Return whether or not this project supports translations."""
        return self.versioning_scheme == MULTIPLE_VERSIONS_WITH_TRANSLATIONS

    def subdomain(self, use_canonical_domain=True, resolver=None):
        """Get project subdomain from resolver."""
        resolver = resolver or Resolver()
        return resolver.get_domain_without_protocol(self, use_canonical_domain=use_canonical_domain)

    def get_downloads(self, resolver=None):
        downloads = {}
        default_version = self.get_default_version()

        for type_ in ("htmlzip", "epub", "pdf"):
            downloads[type_] = self.get_production_media_url(
                type_,
                default_version,
                resolver=resolver,
            )

        return downloads

    @property
    def clean_repo(self):
        # NOTE: this method is used only when the project is going to be clonned.
        # It probably makes sense to do a data migrations and force "Import Project"
        # form to validate it's an HTTPS URL when importing new ones
        if self.repo.startswith("http://github.com"):
            return self.repo.replace("http://github.com", "https://github.com")
        return self.repo

    @property
    def repository_html_url(self):
        if self.remote_repository:
            return self.remote_repository.html_url

        ssh_url_pattern = re.compile(r"^(?P<user>.+)@(?P<host>.+):(?P<repo>.+)$")
        match = ssh_url_pattern.match(self.repo)
        if match:
            return f"https://{match.group('host')}/{match.group('repo')}"
        return self.repo

    # Doc PATH:
    # MEDIA_ROOT/slug/checkouts/version/<repo>

    @property
    def doc_path(self):
        return os.path.join(settings.DOCROOT, self.slug.replace("_", "-"))

    def checkout_path(self, version=LATEST):
        return os.path.join(self.doc_path, "checkouts", version)

    def full_doc_path(self, version=LATEST):
        """The path to the documentation root in the project."""
        doc_base = self.checkout_path(version)
        for possible_path in ["docs", "doc", "Doc"]:
            if os.path.exists(os.path.join(doc_base, "%s" % possible_path)):
                return os.path.join(doc_base, "%s" % possible_path)
        # No docs directory, docs are at top-level.
        return doc_base

    def artifact_path(self, type_, version=LATEST):
        """
        The path to the build docs output for the project.

        :param type_: one of `html`, `json`, `htmlzip`, `pdf`, `epub`.
        :param version: slug of the version.
        """
        return os.path.join(self.checkout_path(version=version), "_readthedocs", type_)

    def conf_file(self, version=LATEST):
        """Find a Sphinx ``conf.py`` file in the project checkout."""
        files = self.find("conf.py", version)
        if not files:
            files = self.full_find("conf.py", version)
        if len(files) == 1:
            return files[0]
        for filename in files:
            # When multiples conf.py files, we look up the first one that
            # contains the `doc` word in its path and return this one
            if filename.find("doc", 70) != -1:
                return filename

        # If the project has more than one conf.py file but none of them have
        # the `doc` word in the path, we raise an error informing this to the user
        if len(files) > 1:
            raise ProjectConfigurationError(
                ProjectConfigurationError.MULTIPLE_CONF_FILES,
            )

        raise ProjectConfigurationError(ProjectConfigurationError.NOT_FOUND)

    def conf_dir(self, version=LATEST):
        conf_file = self.conf_file(version)
        if conf_file:
            return os.path.dirname(conf_file)

    @property
    def has_good_build(self):
        # Check if there is `_has_good_build` annotation in the queryset.
        # Used for database optimization.
        if hasattr(self, "_has_good_build"):
            return self._has_good_build
        return self.builds(manager=INTERNAL).filter(success=True).exists()

    def vcs_repo(self, environment, version):
        """
        Return a Backend object for this project able to handle VCS commands.

        :param environment: environment to run the commands
        :type environment: doc_builder.environments.BuildEnvironment
        :param version: Version for the backend.
        """
        backend = self.vcs_class()
        if not backend:
            repo = None
        else:
            repo = backend(
                self,
                version=version,
                environment=environment,
                use_token=bool(self.clone_token),
            )
        return repo

    def vcs_class(self):
        """
        Get the class used for VCS operations.

        This is useful when doing operations that don't need to have the repository on disk.
        """
        return backend_cls.get(self.repo_type)

    def _guess_service_class(self):
        from readthedocs.oauth.services import registry

        for service_cls in registry:
            if service_cls.is_project_service(self):
                return service_cls
        return None

    def get_git_service_class(self, fallback_to_clone_url=False):
        """
        Get the service class for project. e.g: GitHubService, GitLabService.

        :param fallback_to_clone_url: If the project doesn't have a remote repository,
         we try to guess the service class based on the clone URL.
        """
        service_cls = None
        if self.has_feature(Feature.DONT_SYNC_WITH_REMOTE_REPO):
            return self._guess_service_class()
        service_cls = self.remote_repository and self.remote_repository.get_service_class()
        if not service_cls and fallback_to_clone_url:
            return self._guess_service_class()
        return service_cls

    @property
    def is_github_project(self):
        from readthedocs.oauth.services import GitHubAppService
        from readthedocs.oauth.services import GitHubService

        return self.get_git_service_class(fallback_to_clone_url=True) in [
            GitHubService,
            GitHubAppService,
        ]

    @property
    def is_github_app_project(self):
        return self.remote_repository and self.remote_repository.vcs_provider == GITHUB_APP

    @property
    def old_github_remote_repository(self):
        """
        Get the old GitHub OAuth repository for GitHub App projects.

        This is mainly used for projects that migrated to the new GitHub App,
        but its users have not yet connected their accounts to the new GitHub App.
        We still need to reference the old repository for permissions when using GH as SSO method.
        """
        from readthedocs.oauth.models import RemoteRepository

        if self.is_github_app_project:
            return RemoteRepository.objects.filter(
                vcs_provider=GITHUB,
                remote_id=self.remote_repository.remote_id,
            ).first()
        return None

    @property
    def is_gitlab_project(self):
        from readthedocs.oauth.services import GitLabService

        return self.get_git_service_class(fallback_to_clone_url=True) == GitLabService

    @property
    def is_bitbucket_project(self):
        from readthedocs.oauth.services import BitbucketService

        return self.get_git_service_class(fallback_to_clone_url=True) == BitbucketService

    def find(self, filename, version):
        """
        Find files inside the project's ``doc`` path.

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.full_doc_path(version)):
            for match in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, match))
        return matches

    def full_find(self, filename, version):
        """
        Find files inside a project's checkout path.

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.checkout_path(version)):
            for match in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, match))
        return matches

    @cached_property
    def latest_internal_build(self):
        """Get the latest internal build for the project."""
        return self.builds(manager=INTERNAL).select_related("version").first()

    def active_versions(self):
        versions = self.versions(manager=INTERNAL).public(only_active=True)
        return versions.filter(built=True, active=True) | versions.filter(
            active=True, uploaded=True
        )

    def all_active_versions(self):
        """
        Get queryset with all active versions.

        .. note::
            This is a temporary workaround for activate_versions filtering out
            things that were active, but failed to build

        :returns: :py:class:`Version` queryset
        """
        return self.versions(manager=INTERNAL).filter(active=True)

    def get_stable_version(self):
        return self.versions.filter(slug=STABLE).first()

    def get_original_stable_version(self):
        """
        Get the original version that stable points to.

        When stable is machine created, it's basically an alias
        for the latest stable version (like 2.2),
        that version is the "original" one.

        Returns None if the current stable doesn't point to a valid version
        or if isn't machine created.
        """
        current_stable = self.get_stable_version()
        if not current_stable or not current_stable.machine:
            return None
        # Several tags can point to the same identifier.
        # Return the stable one.
        original_stable = determine_stable_version(
            self.versions(manager=INTERNAL).filter(identifier=current_stable.identifier)
        )
        return original_stable

    def get_latest_version(self):
        return self.versions.filter(slug=LATEST).first()

    def get_original_latest_version(self):
        """
        Get the original version that latest points to.

        When latest is machine created, it's basically an alias
        for the default branch/tag (like main/master),

        Returns None if latest doesn't point to a valid version,
        or if isn't managed by RTD (machine=False).
        """
        # For latest, the identifier is the name of the branch/tag.
        latest_version_identifier = (
            self.versions.filter(slug=LATEST, machine=True)
            .values_list("identifier", flat=True)
            .first()
        )
        if not latest_version_identifier:
            return None
        return (
            self.versions(manager=INTERNAL)
            .exclude(slug=LATEST)
            .filter(verbose_name=latest_version_identifier)
            .first()
        )

    def update_latest_version(self):
        """
        If the current latest version is machine created, update it.

        A machine created LATEST version is an alias for the default branch/tag,
        so we need to update it to match the type and identifier of the default branch/tag.
        """
        latest = self.get_latest_version()
        if not latest:
            latest = self.versions.create_latest()
        if not latest.machine:
            return

        # default_branch can be a tag or a branch name!
        default_version_name = self.get_default_branch(fallback_to_vcs=False)
        # If the default_branch is not set, it means that the user
        # wants to use the default branch of the respository, but
        # we don't know what that is here, `latest` will be updated
        # on the next build.
        if not default_version_name:
            return

        # Search for a branch or tag with the name of the default branch,
        # so we can sync latest with it.
        original_latest = (
            self.versions(manager=INTERNAL)
            .exclude(slug=LATEST)
            .filter(verbose_name=default_version_name)
            .first()
        )
        latest.verbose_name = LATEST_VERBOSE_NAME
        latest.type = original_latest.type if original_latest else BRANCH
        # For latest, the identifier is the name of the branch/tag.
        latest.identifier = default_version_name
        latest.save()
        return latest

    def update_stable_version(self):
        """
        Returns the version that was promoted to be the new stable version.

        Return ``None`` if no update was made or if there is no version on the
        project that can be considered stable.
        """

        # return immediately if the current stable is managed by the user and
        # not automatically by Read the Docs (``machine=False``)
        current_stable = self.get_stable_version()
        if current_stable and not current_stable.machine:
            return None

        versions = self.versions(manager=INTERNAL).all()
        new_stable = determine_stable_version(versions)
        if new_stable:
            if current_stable:
                version_updated = (
                    new_stable.identifier != current_stable.identifier
                    or new_stable.type != current_stable.type
                    or current_stable.verbose_name != STABLE_VERBOSE_NAME
                )
                if version_updated:
                    log.info(
                        "Stable version updated.",
                        project_slug=self.slug,
                        version_identifier=new_stable.identifier,
                        version_type=new_stable.type,
                    )
                    current_stable.identifier = new_stable.identifier
                    current_stable.verbose_name = STABLE_VERBOSE_NAME
                    current_stable.type = new_stable.type
                    current_stable.save()
                    return new_stable
            else:
                log.info(
                    "Creating new stable version",
                    project_slug=self.slug,
                    version_identifier=new_stable.identifier,
                )
                current_stable = self.versions.create_stable(
                    type=new_stable.type,
                    identifier=new_stable.identifier,
                )
                return new_stable

    def versions_from_name(self, name, type=None):
        """
        Get all versions attached to the branch or tag name.

        Normally, only one version should be returned, but since LATEST and STABLE
        are aliases for the branch/tag, they may be returned as well.

        If type is None, both, tags and branches will be taken into consideration.
        """
        queryset = self.versions(manager=INTERNAL)
        queryset = queryset.filter(
            # Normal branches
            Q(verbose_name=name, machine=False)
            # Latest and stable have the name of the branch/tag in the identifier.
            # NOTE: if stable is a branch, identifier will be the commit hash,
            # so we don't have a way to match it by name.
            # We should do another lookup to get the original stable version,
            # or change our logic to store the tags name in the identifier of stable.
            | Q(identifier=name, machine=True)
        )

        if type:
            queryset = queryset.filter(type=type)

        return queryset.distinct()

    def get_default_version(self):
        """
        Get the default version (slug).

        Returns self.default_version if the version with that slug actually
        exists (is built and published). Otherwise returns 'latest'.
        """
        # latest is a special case where we don't have to check if it exists
        if self.default_version == LATEST:
            return self.default_version
        # check if the default_version exists
        version_qs = self.versions.filter(
            slug=self.default_version,
            active=True,
        )
        if version_qs.exists():
            return self.default_version
        return LATEST

    def get_default_branch(self, fallback_to_vcs=True):
        """
        Get the name of the branch or tag that the user wants to use as 'latest'.

        In case the user explicitly set a default branch, we use that,
        otherwise we try to get it from the remote repository.
        """
        if self.default_branch:
            return self.default_branch

        if self.remote_repository and self.remote_repository.default_branch:
            return self.remote_repository.default_branch

        if not fallback_to_vcs:
            return None

        vcs_class = self.vcs_class()
        if vcs_class:
            return vcs_class.fallback_branch
        return "Unknown"

    def add_subproject(self, child, alias=None):
        subproject, _ = ProjectRelationship.objects.get_or_create(
            parent=self,
            child=child,
            alias=alias,
        )
        return subproject

    def remove_subproject(self, child):
        ProjectRelationship.objects.filter(parent=self, child=child).delete()

    @cached_property
    def parent_relationship(self):
        """
        Get parent project relationship.

        It returns ``None`` if this is a top level project.
        """
        if hasattr(self, "_superprojects"):
            # Cached parent project relationship
            if self._superprojects:
                return self._superprojects[0]
            return None

        return self.superprojects.select_related("parent").first()

    @cached_property
    def canonical_custom_domain(self):
        """Get the canonical custom domain or None."""
        if hasattr(self, "_canonical_domains"):
            # Cached custom domains
            if self._canonical_domains:
                return self._canonical_domains[0]
            return None

        return self.domains.filter(canonical=True).first()

    @property
    def features(self):
        return Feature.objects.for_project(self)

    def has_feature(self, feature_id):
        """
        Does project have existing feature flag.

        If the feature has a historical True value before the feature was added,
        we consider the project to have the flag. This is used for deprecating a
        feature or changing behavior for new projects
        """
        return self.features.filter(feature_id=feature_id).exists()

    def get_feature_value(self, feature, positive, negative):
        """
        Look up project feature, return corresponding value.

        If a project has a feature, return ``positive``, otherwise return
        ``negative``
        """
        return positive if self.has_feature(feature) else negative

    @property
    def show_advertising(self):
        """
        Whether this project is ad-free.

        :returns: ``True`` if advertising should be shown and ``False`` otherwise
        :rtype: bool
        """
        if self.ad_free or self.gold_owners.exists():
            return False

        if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import is_show_ads_denied  # noqa

            return not is_show_ads_denied(self)

        return True

    def environment_variables(self, *, public_only=True):
        """
        Environment variables to build this particular project.

        :param public_only: Only return publicly visible variables?
        :returns: dictionary with all visible variables {name: value}
        :rtype: dict
        """
        return {
            variable.name: variable.value
            for variable in self.environmentvariable_set.all()
            if variable.public or not public_only
        }

    def is_valid_as_superproject(self, error_class):
        """
        Checks if the project can be a superproject.

        This is used to handle form and serializer validations
        if check fails returns ValidationError using to the error_class passed
        """
        # Check the parent project is not a subproject already
        if self.superprojects.exists():
            raise error_class(
                _("Subproject nesting is not supported"),
            )

    def get_subproject_candidates(self, user):
        """
        Get a queryset of projects that would be valid as a subproject for this project.

        This excludes:

        - The project itself
        - Projects that are already a subproject of another project
        - Projects that are a superproject.

        If the project belongs to an organization,
        we only allow projects under the same organization as subprojects,
        otherwise only projects that don't belong to an organization.

        Both projects need to share the same owner/admin.
        """
        organization = self.organizations.first()
        queryset = (
            Project.objects.for_admin_user(user)
            .filter(organizations=organization)
            .exclude(subprojects__isnull=False)
            .exclude(superprojects__isnull=False)
            .exclude(pk=self.pk)
        )
        return queryset

    @property
    def organization(self):
        return self.organizations.first()

    @property
    def clone_token(self) -> str | None:
        """
        Return a HTTP-based Git access token to the repository.

        .. note::

           - A token is only returned for projects linked to a private repository.
           - Only repositories granted access by a GitHub app installation will return a token.
        """
        service_class = self.get_git_service_class()
        if not service_class or not self.remote_repository.private:
            return None

        if not service_class.supports_clone_token:
            return None

        for service in service_class.for_project(self):
            token = service.get_clone_token(self)
            if token:
                return token
        return None


class APIProject(Project):
    """
    Project proxy model for API data deserialization.

    This replaces the pattern where API data was deserialized into a mocked
    :py:class:`Project` object. This pattern was confusing, as it was not explicit
    as to what form of object you were working with -- API backed or database
    backed.

    This model preserves the Project model methods, allowing for overrides on
    model field differences. This model pattern will generally only be used on
    builder instances, where we are interacting solely with API data.
    """

    features = []
    # This is a property in the original model, in order to
    # be able to assign it a value in the constructor, we need to re-declare it
    # as an attribute here.
    clone_token = None

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self.features = kwargs.pop("features", [])
        self.clone_token = kwargs.pop("clone_token", None)
        environment_variables = kwargs.pop("environment_variables", {})
        ad_free = not kwargs.pop("show_advertising", True)
        # These fields only exist on the API return, not on the model, so we'll
        # remove them to avoid throwing exceptions due to unexpected fields
        for key in [
            "users",
            "resource_uri",
            "absolute_url",
            "downloads",
            "main_language_project",
            "related_projects",
        ]:
            try:
                del kwargs[key]
            except KeyError:
                pass

        valid_attributes, invalid_attributes = extract_valid_attributes_for_model(
            model=Project,
            attributes=kwargs,
        )
        if invalid_attributes:
            log.warning(
                "APIProject got unexpected attributes.",
                invalid_attributes=invalid_attributes,
            )

        super().__init__(*args, **valid_attributes)

        # Overwrite the database property with the value from the API
        self.ad_free = ad_free
        self._environment_variables = environment_variables

    def save(self, *args, **kwargs):
        return 0

    def has_feature(self, feature_id):
        return feature_id in self.features

    @property
    def show_advertising(self):
        """Whether this project is ad-free (don't access the database)."""
        return not self.ad_free

    def environment_variables(self, *, public_only=True):
        return {
            name: spec["value"]
            for name, spec in self._environment_variables.items()
            if spec["public"] or not public_only
        }


class ImportedFile(models.Model):
    """
    Imported files model.

    This tracks files that are output from documentation builds, useful for
    things like CDN invalidation.
    """

    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(
        Project,
        verbose_name=_("Project"),
        related_name="imported_files",
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        "builds.Version",
        verbose_name=_("Version"),
        related_name="imported_files",
        null=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("Name"), max_length=255)

    # max_length is set to 4096 because linux has a maximum path length
    # of 4096 characters for most filesystems (including EXT4).
    # https://github.com/rtfd/readthedocs.org/issues/5061
    path = models.CharField(_("Path"), max_length=4096)
    commit = models.CharField(_("Commit"), max_length=255)
    build = models.IntegerField(_("Build id"), null=True)
    modified_date = models.DateTimeField(_("Modified date"), auto_now=True)
    rank = models.IntegerField(
        _("Page search rank"),
        default=0,
        validators=[MinValueValidator(-10), MaxValueValidator(10)],
    )
    ignore = models.BooleanField(
        _("Ignore this file from operations like indexing"),
        # default=False,
        # TODO: remove after migration
        null=True,
    )

    def get_absolute_url(self):
        return Resolver().resolve_version(
            project=self.project,
            version=self.version.slug,
            filename=self.path,
        )


class HTMLFile(ImportedFile):
    """
    Imported HTML file Proxy model.

    This tracks only the HTML files for indexing to search.
    """

    class Meta:
        proxy = True

    objects = HTMLFileManager()

    def get_processed_json(self):
        parser = GenericParser(self.version)
        return parser.parse(self.path)

    @cached_property
    def processed_json(self):
        return self.get_processed_json()


class Notification(TimeStampedModel):
    """WebHook / Email notification attached to a Project."""

    # TODO: Overridden from TimeStampedModel just to allow null values,
    # remove after deploy.
    created = CreationDateTimeField(
        _("created"),
        null=True,
        blank=True,
    )
    modified = ModificationDateTimeField(
        _("modified"),
        null=True,
        blank=True,
    )

    project = models.ForeignKey(
        Project,
        related_name="%(class)s_notifications",
        on_delete=models.CASCADE,
    )
    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        abstract = True


class EmailHook(Notification):
    email = models.EmailField()

    def __str__(self):
        return self.email


class WebHookEvent(models.Model):
    BUILD_TRIGGERED = "build:triggered"
    BUILD_PASSED = "build:passed"
    BUILD_FAILED = "build:failed"

    EVENTS = (
        (BUILD_TRIGGERED, _("Build triggered")),
        (BUILD_PASSED, _("Build passed")),
        (BUILD_FAILED, _("Build failed")),
    )

    name = models.CharField(
        max_length=256,
        unique=True,
        choices=EVENTS,
    )

    def __str__(self):
        return self.name


class WebHook(Notification):
    url = models.URLField(
        _("URL"),
        max_length=600,
        help_text=_("URL to send the webhook to"),
    )
    secret = models.CharField(
        help_text=_("Secret used to sign the payload of the webhook"),
        max_length=255,
        blank=True,
        null=True,
    )
    events = models.ManyToManyField(
        WebHookEvent,
        related_name="webhooks",
        help_text=_("Events to subscribe"),
    )
    payload = models.TextField(
        _("JSON payload"),
        help_text=_(
            "JSON payload to send to the webhook. "
            'Check <a href="https://docs.readthedocs.io/page/build-notifications.html#variable-substitutions-reference">the docs</a> for available substitutions.',  # noqa
        ),
        blank=True,
        null=True,
        max_length=25000,
    )
    exchanges = GenericRelation(
        "integrations.HttpExchange",
        related_query_name="webhook",
    )

    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = get_random_string(length=32)
        super().save(*args, **kwargs)

    def get_payload(self, version, build, event):
        """
        Get the final payload replacing all placeholders.

        Placeholders are in the ``{{ foo }}`` or ``{{foo}}`` format.
        """
        if not self.payload:
            return None

        project = version.project
        organization = project.organizations.first()

        organization_name = ""
        organization_slug = ""
        if organization:
            organization_slug = organization.slug
            organization_name = organization.name

        # Commit can be None, display an empty string instead.
        commit = build.commit or ""
        protocol = "http" if settings.DEBUG else "https"
        project_url = f"{protocol}://{settings.PRODUCTION_DOMAIN}{project.get_absolute_url()}"
        build_url = f"{protocol}://{settings.PRODUCTION_DOMAIN}{build.get_absolute_url()}"
        build_docsurl = Resolver().resolve_version(project, version=version)

        # Remove timezone and microseconds from the date,
        # so it's more readable.
        start_date = build.date.replace(tzinfo=None, microsecond=0).isoformat()

        substitutions = {
            "event": event,
            "build.id": build.id,
            "build.commit": commit,
            "build.url": build_url,
            "build.docs_url": build_docsurl,
            "build.start_date": start_date,
            "organization.name": organization_name,
            "organization.slug": organization_slug,
            "project.slug": project.slug,
            "project.name": project.name,
            "project.url": project_url,
            "version.slug": version.slug,
            "version.name": version.verbose_name,
        }
        payload = self.payload
        # Small protection for DDoS.
        max_substitutions = 99
        for substitution, value in substitutions.items():
            # Replace {{ foo }}.
            payload = payload.replace(f"{{{{ {substitution} }}}}", str(value), max_substitutions)
            # Replace {{foo}}.
            payload = payload.replace(f"{{{{{substitution}}}}}", str(value), max_substitutions)
        return payload

    def sign_payload(self, payload):
        """Get the signature of `payload` using HMAC-SHA1 with the webhook secret."""
        digest = hmac.new(
            key=self.secret.encode(),
            msg=payload.encode(),
            digestmod=hashlib.sha256,
        )
        return digest.hexdigest()


class Domain(TimeStampedModel):
    """A custom domain name for a project."""

    # TODO: Overridden from TimeStampedModel just to allow null values,
    # remove after deploy.
    created = CreationDateTimeField(
        _("created"),
        null=True,
        blank=True,
    )

    project = models.ForeignKey(
        Project,
        related_name="domains",
        on_delete=models.CASCADE,
    )
    domain = models.CharField(
        _("Domain"),
        unique=True,
        max_length=255,
        validators=[validate_domain_name, validate_no_ip],
    )
    machine = models.BooleanField(
        default=False,
        help_text=_("This domain was auto-created"),
    )
    cname = models.BooleanField(
        default=False,
        help_text=_("This domain is a CNAME for the project"),
    )
    canonical = models.BooleanField(
        default=False,
        help_text=_(
            "This domain is the primary one where the documentation is served from",
        ),
    )
    https = models.BooleanField(
        _("Use HTTPS"),
        default=True,
        help_text=_("Always use HTTPS for this domain"),
    )
    count = models.IntegerField(
        default=0,
        help_text=_("Number of times this domain has been hit"),
    )

    # This is used in readthedocsext.
    ssl_status = models.CharField(
        _("SSL certificate status"),
        max_length=30,
        choices=constants.SSL_STATUS_CHOICES,
        default=constants.SSL_STATUS_UNKNOWN,
        # Remove after deploy
        null=True,
        blank=True,
    )
    skip_validation = models.BooleanField(
        _("Skip validation process."),
        default=False,
    )
    validation_process_start = models.DateTimeField(
        _("Start date of the validation process."),
        auto_now_add=True,
    )

    # Strict-Transport-Security header options
    # These are not exposed to users because it's easy to misconfigure things
    # and hard to back out changes cleanly
    hsts_max_age = models.PositiveIntegerField(
        default=0,
        help_text=_("Set a custom max-age (eg. 31536000) for the HSTS header"),
    )
    hsts_include_subdomains = models.BooleanField(
        default=False,
        help_text=_("If hsts_max_age > 0, set the includeSubDomains flag with the HSTS header"),
    )
    hsts_preload = models.BooleanField(
        default=False,
        help_text=_("If hsts_max_age > 0, set the preload flag with the HSTS header"),
    )

    objects = DomainQueryset.as_manager()

    class Meta:
        ordering = ("-canonical", "-machine", "domain")

    def __str__(self):
        return self.domain

    @property
    def is_valid(self):
        return self.ssl_status == constants.SSL_STATUS_VALID

    @property
    def validation_process_expiration_date(self):
        return self.validation_process_start.date() + timezone.timedelta(
            days=settings.RTD_CUSTOM_DOMAINS_VALIDATION_PERIOD
        )

    @property
    def validation_process_expired(self):
        return timezone.now().date() >= self.validation_process_expiration_date

    def restart_validation_process(self):
        """Restart the validation process if it has expired."""
        if not self.is_valid and self.validation_process_expired:
            self.validation_process_start = timezone.now()
            self.save()

    def clean(self):
        # Only check the limit when creating a new domain,
        # not when updating existing ones.
        if not self.pk:
            check_domains_limit(self.project)

    def save(self, *args, **kwargs):
        parsed = urlparse(self.domain)
        if parsed.scheme or parsed.netloc:
            self.domain = parsed.netloc
        else:
            self.domain = parsed.path
        super().save(*args, **kwargs)


class HTTPHeader(TimeStampedModel, models.Model):
    """
    Define a HTTP header for a user Domain.

    All the HTTPHeader(s) associated with the domain are added in the response
    from El Proxito.

    NOTE: the available headers are hardcoded in the NGINX configuration for
    now (see ``dockerfile/nginx/proxito.conf``) until we figure it out a way to
    expose them all without hardcoding them.
    """

    HEADERS_CHOICES = (
        ("access_control_allow_origin", "Access-Control-Allow-Origin"),
        ("access_control_allow_headers", "Access-Control-Allow-Headers"),
        ("access_control_expose_headers", "Access-Control-Expose-Headers"),
        ("content_security_policy", "Content-Security-Policy"),
        ("feature_policy", "Feature-Policy"),
        ("permissions_policy", "Permissions-Policy"),
        ("referrer_policy", "Referrer-Policy"),
        ("x_frame_options", "X-Frame-Options"),
        ("x_content_type_options", "X-Content-Type-Options"),
    )

    domain = models.ForeignKey(
        Domain,
        related_name="http_headers",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=128,
        choices=HEADERS_CHOICES,
    )
    value = models.CharField(max_length=4096)
    only_if_secure_request = models.BooleanField(
        help_text="Only set this header if the request is secure (HTTPS)",
    )

    def __str__(self):
        return self.name


class Feature(models.Model):
    """
    Project feature flags.

    Features should generally be added here as choices, however features may
    also be added dynamically from a signal in other packages. Features can be
    added by external packages with the use of signals::

        @receiver(pre_init, sender=Feature)
        def add_features(sender, **kwargs):
            sender.FEATURES += (('blah', 'BLAH'),)

    The FeatureForm will grab the updated list on instantiation.
    """

    # Feature constants - this is not a exhaustive list of features, features
    # may be added by other packages
    DISABLE_PAGEVIEWS = "disable_pageviews"
    RESOLVE_PROJECT_FROM_HEADER = "resolve_project_from_header"
    USE_PROXIED_APIS_WITH_PREFIX = "use_proxied_apis_with_prefix"
    ALLOW_VERSION_WARNING_BANNER = "allow_version_warning_banner"
    DONT_SYNC_WITH_REMOTE_REPO = "dont_sync_with_remote_repo"

    # Versions sync related features
    SKIP_SYNC_TAGS = "skip_sync_tags"
    SKIP_SYNC_BRANCHES = "skip_sync_branches"
    SKIP_SYNC_VERSIONS = "skip_sync_versions"

    # Dependencies related features
    PIP_ALWAYS_UPGRADE = "pip_always_upgrade"

    # Search related features
    DEFAULT_TO_FUZZY_SEARCH = "default_to_fuzzy_search"

    # Build related features
    SCALE_IN_PROTECTION = "scale_in_prtection"
    USE_S3_SCOPED_CREDENTIALS_ON_BUILDERS = "use_s3_scoped_credentials_on_builders"
    BUILD_FULL_CLEAN = "build_full_clean"
    BUILD_HEALTHCHECK = "build_healthcheck"
    BUILD_NO_ACKS_LATE = "build_no_acks_late"

    FEATURES = (
        (
            DISABLE_PAGEVIEWS,
            _("Proxito: Disable all page views"),
        ),
        (
            RESOLVE_PROJECT_FROM_HEADER,
            _("Proxito: Allow usage of the X-RTD-Slug header"),
        ),
        (
            USE_PROXIED_APIS_WITH_PREFIX,
            _(
                "Proxito: Use proxied APIs (/_/*) with the custom prefix if the project has one (Project.custom_prefix)."
            ),
        ),
        (
            ALLOW_VERSION_WARNING_BANNER,
            _("Dashboard: Allow project to use the version warning banner."),
        ),
        (
            DONT_SYNC_WITH_REMOTE_REPO,
            _("Remote repository: Don't keep project in sync with remote repository."),
        ),
        # Versions sync related features
        (
            SKIP_SYNC_BRANCHES,
            _("Webhook: Skip syncing branches"),
        ),
        (
            SKIP_SYNC_TAGS,
            _("Webhook: Skip syncing tags"),
        ),
        (
            SKIP_SYNC_VERSIONS,
            _("Webhook: Skip sync versions task"),
        ),
        # Dependencies related features
        (PIP_ALWAYS_UPGRADE, _("Build: Always run pip install --upgrade")),
        # Search related features.
        (
            DEFAULT_TO_FUZZY_SEARCH,
            _("Search: Default to fuzzy search for simple search queries"),
        ),
        # Build related features.
        (
            SCALE_IN_PROTECTION,
            _("Build: Set scale-in protection before/after building."),
        ),
        (
            USE_S3_SCOPED_CREDENTIALS_ON_BUILDERS,
            _("Build: Use S3 scoped credentials for uploading build artifacts."),
        ),
        (
            BUILD_FULL_CLEAN,
            _("Build: Clean all build directories to avoid leftovers from other projects."),
        ),
        (
            BUILD_HEALTHCHECK,
            _("Build: Use background cURL healthcheck."),
        ),
        (
            BUILD_NO_ACKS_LATE,
            _("Build: Do not use Celery ASK_LATE config for this project."),
        ),
    )

    FEATURES = sorted(FEATURES, key=lambda x: x[1])

    projects = models.ManyToManyField(
        Project,
        blank=True,
    )
    # Feature is not implemented as a ChoiceField, as we don't want validation
    # at the database level on this field. Arbitrary values are allowed here.
    feature_id = models.CharField(
        _("Feature identifier"),
        max_length=255,
        unique=True,
    )
    add_date = models.DateTimeField(
        _("Date feature was added"),
        auto_now_add=True,
    )
    # TODO: rename this field to `past_default_true` and follow this steps when deploying
    # https://github.com/readthedocs/readthedocs.org/pull/7524#issuecomment-703663724
    default_true = models.BooleanField(
        _("Default all past projects to True"),
        default=False,
    )
    future_default_true = models.BooleanField(
        _("Default all future projects to True"),
        default=False,
    )

    objects = FeatureQuerySet.as_manager()

    def __str__(self):
        return self.get_feature_display()

    def get_feature_display(self):
        """
        Implement display name field for fake ChoiceField.

        Because the field is not a ChoiceField here, we need to manually
        implement this behavior.
        """
        return str(dict(self.FEATURES).get(self.feature_id, self.feature_id))


class EnvironmentVariable(TimeStampedModel, models.Model):
    name = models.CharField(
        max_length=128,
        help_text=_("Name of the environment variable"),
    )
    value = models.CharField(
        max_length=48000,
        help_text=_("Value of the environment variable"),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        help_text=_("Project where this variable will be used"),
    )
    public = models.BooleanField(
        _("Public"),
        default=False,
        null=True,
        help_text=_("Expose this environment variable in PR builds?"),
    )

    objects = RelatedProjectQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.value = quote(self.value)
        return super().save(*args, **kwargs)

    def clean(self):
        validate_environment_variable_size(project=self.project, new_env_value=self.value)
        return super().clean()
