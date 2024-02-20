"""Project models."""
import fnmatch
import hashlib
import hmac
import os
from shlex import quote
from urllib.parse import urlparse

import structlog
from allauth.socialaccount.providers import registry as allauth_registry
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from django_extensions.db.models import TimeStampedModel
from taggit.managers import TaggableManager

from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    INTERNAL,
    LATEST,
    LATEST_VERBOSE_NAME,
    STABLE,
)
from readthedocs.core.history import ExtraHistoricalRecords
from readthedocs.core.resolver import Resolver
from readthedocs.core.utils import extract_valid_attributes_for_model, slugify
from readthedocs.core.utils.url import unsafe_join_url_path
from readthedocs.domains.querysets import DomainQueryset
from readthedocs.notifications.models import Notification as NewNotification
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.managers import HTMLFileManager
from readthedocs.projects.querysets import (
    ChildRelatedProjectQuerySet,
    FeatureQuerySet,
    ProjectQuerySet,
    RelatedProjectQuerySet,
)
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.projects.validators import (
    validate_build_config_file,
    validate_custom_prefix,
    validate_custom_subproject_prefix,
    validate_domain_name,
    validate_no_ip,
    validate_repository_url,
)
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.search.parsers import GenericParser
from readthedocs.storage import build_media_storage
from readthedocs.vcs_support.backends import backend_cls

from .constants import (
    DOWNLOADABLE_MEDIA_TYPES,
    MEDIA_TYPES,
    MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
    MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
    PRIVATE,
    PUBLIC,
)

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

    def __str__(self):
        return "{} -> {}".format(self.parent, self.child)

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

    DOC_DIFF_DEFAULT_ROOT_SELECTOR = "[role=main]"

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

    # Analytics

    # NOTE: we keep analytics disabled by default to save resources.
    # Most projects won't be taking a look at these numbers.
    analytics_enabled = models.BooleanField(default=False)

    # Docdiff
    doc_diff_enabled = models.BooleanField(default=True)
    doc_diff_show_additions = models.BooleanField(default=True)
    doc_diff_show_deletions = models.BooleanField(default=True)
    doc_diff_root_selector = models.CharField(null=True, blank=True, max_length=128)

    # External version warning
    external_version_warning_enabled = models.BooleanField(default=True)

    # EthicalAds
    ethicalads_enabled = models.BooleanField(default=True)

    # Flyout
    flyout_enabled = models.BooleanField(default=True)

    # Hotkeys
    hotkeys_enabled = models.BooleanField(default=True)

    # Search
    search_enabled = models.BooleanField(default=True)
    search_default_filter = models.CharField(null=True, blank=True, max_length=128)

    # Stable/Latest version warning
    stable_latest_version_warning_enabled = models.BooleanField(default=True)


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
    pub_date = models.DateTimeField(
        _("Publication date"), auto_now_add=True, db_index=True
    )
    modified_date = models.DateTimeField(
        _("Modified date"), auto_now=True, db_index=True
    )

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
    repo = models.CharField(
        _("Repository URL"),
        max_length=255,
        validators=[validate_repository_url],
        help_text=_("Hosted documentation repository URL"),
        db_index=True,
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
        _("Versioning scheme"),
        max_length=120,
        default=constants.MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
        choices=constants.VERSIONING_SCHEME_CHOICES,
        # TODO: remove after migration
        null=True,
        help_text=_(
            "This affects how the URL of your documentation looks like, "
            "and if it supports translations or multiple versions. "
            "Changing the versioning scheme will break your current URLs."
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
            'What branch "latest" points to. Leave empty '
            "to use the default value for your VCS.",
        ),
    )
    requirements_file = models.CharField(
        _("Requirements file"),
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            "A <a "
            'href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">'
            "pip requirements file</a> needed to build your documentation. "
            "Path from the root of your project.",
        ),
    )
    documentation_type = models.CharField(
        _("Documentation type"),
        max_length=20,
        choices=constants.DOCUMENTATION_CHOICES,
        default="sphinx",
        help_text=_(
            'Type of documentation you are building. <a href="'
            "http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html."
            'DirectoryHTMLBuilder">More info on sphinx builders</a>.',
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
            "Memory limit in Docker format "
            "-- example: <code>512m</code> or <code>1g</code>",
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
    history = ExtraHistoricalRecords()
    objects = ProjectQuerySet.as_manager()

    remote_repository = models.ForeignKey(
        "oauth.RemoteRepository",
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

    # TODO: remove the following fields since they all are going to be ignored
    # by the application when we start requiring a ``.readthedocs.yaml`` file.
    # These fields are:
    #  - requirements_file
    #  - documentation_type
    #  - enable_epub_build
    #  - enable_pdf_build
    #  - path
    #  - conf_py_file
    #  - install_project
    #  - python_interpreter
    #  - use_system_packages
    requirements_file = models.CharField(
        _("Requirements file"),
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            "A <a "
            'href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">'
            "pip requirements file</a> needed to build your documentation. "
            "Path from the root of your project.",
        ),
    )
    documentation_type = models.CharField(
        _("Documentation type"),
        max_length=20,
        choices=constants.DOCUMENTATION_CHOICES,
        default="sphinx",
        help_text=_(
            'Type of documentation you are building. <a href="'
            "http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html."
            'DirectoryHTMLBuilder">More info on sphinx builders</a>.',
        ),
    )
    enable_epub_build = models.BooleanField(
        _("Enable EPUB build"),
        default=False,
        help_text=_(
            "Create a EPUB version of your documentation with each build.",
        ),
    )
    enable_pdf_build = models.BooleanField(
        _("Enable PDF build"),
        default=False,
        help_text=_(
            "Create a PDF version of your documentation with each build.",
        ),
    )
    path = models.CharField(
        _("Path"),
        max_length=255,
        editable=False,
        help_text=_(
            "The directory where <code>conf.py</code> lives",
        ),
    )
    conf_py_file = models.CharField(
        _("Python configuration file"),
        max_length=255,
        default="",
        blank=True,
        help_text=_(
            "Path from project root to <code>conf.py</code> file "
            "(ex. <code>docs/conf.py</code>). "
            "Leave blank if you want us to find it for you.",
        ),
    )
    install_project = models.BooleanField(
        _("Install Project"),
        help_text=_(
            "Install your project inside a virtualenv using <code>setup.py "
            "install</code>",
        ),
        default=False,
    )
    python_interpreter = models.CharField(
        _("Python Interpreter"),
        max_length=20,
        choices=constants.PYTHON_CHOICES,
        default="python3",
        help_text=_(
            "The Python interpreter used to create the virtual environment.",
        ),
    )
    use_system_packages = models.BooleanField(
        _("Use system packages"),
        help_text=_(
            "Give the virtual environment access to the global site-packages dir.",
        ),
        default=False,
    )

    # Property used for storing the latest build for a project when prefetching
    LATEST_BUILD_CACHE = "_latest_build"

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

        if self.remote_repository:
            privacy_level = PRIVATE if self.remote_repository.private else PUBLIC
            self.external_builds_privacy_level = privacy_level

        super().save(*args, **kwargs)

        try:
            if not self.versions.filter(slug=LATEST).exists():
                self.versions.create_latest()
        except Exception:
            log.exception("Error creating default branches")

        # Update `Version.identifier` for `latest` with the default branch the user has selected,
        # even if it's `None` (meaning to match the `default_branch` of the repository)
        # NOTE: this code is required to be *after* ``create_latest()``.
        # It has to be updated after creating LATEST originally.
        log.debug(
            "Updating default branch.", slug=LATEST, identifier=self.default_branch
        )
        self.versions.filter(slug=LATEST).update(identifier=self.default_branch)

    def delete(self, *args, **kwargs):
        from readthedocs.projects.tasks.utils import clean_project_resources

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

    def get_docs_url(self, version_slug=None, lang_slug=None, external=False):
        """
        Return a URL for the docs.

        ``external`` defaults False because we only link external versions in very specific places
        """
        return Resolver().resolve(
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

    def get_storage_path(
        self, type_, version_slug=LATEST, include_file=True, version_type=None
    ):
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

    def get_production_media_url(self, type_, version_slug):
        """Get the URL for downloading a specific media file."""
        # Use project domain for full path --same domain as docs
        # (project-slug.{PUBLIC_DOMAIN} or docs.project.com)
        domain = self.subdomain()

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
        if self.custom_prefix and self.has_feature(
            Feature.USE_PROXIED_APIS_WITH_PREFIX
        ):
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

    def subdomain(self, use_canonical_domain=True):
        """Get project subdomain from resolver."""
        return Resolver().get_domain_without_protocol(
            self, use_canonical_domain=use_canonical_domain
        )

    def get_downloads(self):
        downloads = {}
        default_version = self.get_default_version()

        for type_ in ("htmlzip", "epub", "pdf"):
            downloads[type_] = self.get_production_media_url(
                type_,
                default_version,
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
        if self.conf_py_file:
            conf_path = os.path.join(
                self.checkout_path(version),
                self.conf_py_file,
            )

            if os.path.exists(conf_path):
                log.info("Inserting conf.py file path from model")
                return conf_path

            log.warning("Conf file specified on model doesn't exist")

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
        # Check if there is `_good_build` annotation in the Queryset.
        # Used for Database optimization.
        if hasattr(self, "_good_build"):
            return self._good_build
        return self.builds(manager=INTERNAL).filter(success=True).exists()

    def vcs_repo(
        self,
        environment,
        version=LATEST,
        verbose_name=None,
        version_type=None,
        version_identifier=None,
        version_machine=None,
    ):
        """
        Return a Backend object for this project able to handle VCS commands.

        :param environment: environment to run the commands
        :type environment: doc_builder.environments.BuildEnvironment
        :param version: version slug for the backend (``LATEST`` by default)
        :type version: str
        """
        # TODO: this seems to be the only method that receives a
        # ``version.slug`` instead of a ``Version`` instance (I prefer an
        # instance here)

        backend = self.vcs_class()
        if not backend:
            repo = None
        else:
            repo = backend(
                self,
                version,
                environment=environment,
                verbose_name=verbose_name,
                version_type=version_type,
                version_identifier=version_identifier,
                version_machine=version_machine,
            )
        return repo

    def vcs_class(self):
        """
        Get the class used for VCS operations.

        This is useful when doing operations that don't need to have the repository on disk.
        """
        return backend_cls.get(self.repo_type)

    def git_service_class(self):
        """Get the service class for project. e.g: GitHubService, GitLabService."""
        from readthedocs.oauth.services import registry

        for service_cls in registry:
            if service_cls.is_project_service(self):
                service = service_cls
                break
        else:
            log.warning("There are no registered services in the application.")
            service = None

        return service

    @property
    def git_provider_name(self):
        """Get the provider name for project. e.g: GitHub, GitLab, Bitbucket."""
        service = self.git_service_class()
        if service:
            provider = allauth_registry.by_id(service.adapter.provider_id)
            return provider.name
        return None

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

    def get_latest_build(self, finished=True):
        """
        Get latest build for project.

        :param finished: Return only builds that are in a finished state
        """
        # Check if there is `_latest_build` attribute in the Queryset.
        # Used for Database optimization.
        if hasattr(self, self.LATEST_BUILD_CACHE):
            if self._latest_build:
                return self._latest_build[0]
            return None

        kwargs = {"type": "html"}
        if finished:
            kwargs["state"] = "finished"
        return self.builds(manager=INTERNAL).filter(**kwargs).first()

    def active_versions(self):
        from readthedocs.builds.models import Version

        versions = Version.internal.public(project=self, only_active=True)
        return versions.filter(built=True, active=True) | versions.filter(
            active=True, uploaded=True
        )

    def ordered_active_versions(self, **kwargs):
        """
        Get all active versions, sorted.

        :param kwargs: All kwargs are passed down to the
                       `Version.internal.public` queryset.
        """
        from readthedocs.builds.models import Version

        kwargs.update(
            {
                "project": self,
                "only_active": True,
                "only_built": True,
            },
        )
        versions = (
            Version.internal.public(**kwargs)
            .select_related(
                "project",
                "project__main_language_project",
            )
            .prefetch_related(
                Prefetch(
                    "project__superprojects",
                    ProjectRelationship.objects.all().select_related("parent"),
                    to_attr="_superprojects",
                ),
                Prefetch(
                    "project__domains",
                    Domain.objects.filter(canonical=True),
                    to_attr="_canonical_domains",
                ),
            )
        )
        return sort_version_aware(versions)

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

        Returns None if the current default version doesn't point to a valid version.
        """
        default_version_name = self.get_default_branch()
        return (
            self.versions(manager=INTERNAL)
            .exclude(slug=LATEST)
            .filter(
                verbose_name=default_version_name,
            )
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
        default_version_name = self.get_default_branch()
        original_latest = self.get_original_latest_version()
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
                )
                if version_updated:
                    log.info(
                        "Stable version updated.",
                        project_slug=self.slug,
                        version_identifier=new_stable.identifier,
                        version_type=new_stable.type,
                    )
                    current_stable.identifier = new_stable.identifier
                    current_stable.type = new_stable.type
                    current_stable.save()
                    return new_stable
            else:
                log.info(
                    "Creating new stable version: %(project)s:%(version)s",
                    {
                        "project": self.slug,
                        "version": new_stable.identifier,
                    },
                )
                current_stable = self.versions.create_stable(
                    type=new_stable.type,
                    identifier=new_stable.identifier,
                )
                return new_stable

    def versions_from_branch_name(self, branch):
        return (
            self.versions.filter(identifier=branch)
            | self.versions.filter(identifier="remotes/origin/%s" % branch)
            | self.versions.filter(identifier="origin/%s" % branch)
            | self.versions.filter(verbose_name=branch)
        )

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

    def get_default_branch(self):
        """Get the version representing 'latest'."""
        if self.default_branch:
            return self.default_branch

        if self.remote_repository and self.remote_repository.default_branch:
            return self.remote_repository.default_branch

        return self.vcs_class().fallback_branch

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

    def get_canonical_custom_domain(self):
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

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self.features = kwargs.pop("features", [])
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

    def __str__(self):
        return "{}: {}".format(self.name, self.project)


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
        project_url = (
            f"{protocol}://{settings.PRODUCTION_DOMAIN}{project.get_absolute_url()}"
        )
        build_url = (
            f"{protocol}://{settings.PRODUCTION_DOMAIN}{build.get_absolute_url()}"
        )
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
            payload = payload.replace(
                f"{{{{ {substitution} }}}}", str(value), max_substitutions
            )
            # Replace {{foo}}.
            payload = payload.replace(
                f"{{{{{substitution}}}}}", str(value), max_substitutions
            )
        return payload

    def sign_payload(self, payload):
        """Get the signature of `payload` using HMAC-SHA1 with the webhook secret."""
        digest = hmac.new(
            key=self.secret.encode(),
            msg=payload.encode(),
            digestmod=hashlib.sha256,
        )
        return digest.hexdigest()

    def __str__(self):
        return f"{self.project.slug} {self.url}"


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
        help_text=_(
            "If hsts_max_age > 0, set the includeSubDomains flag with the HSTS header"
        ),
    )
    hsts_preload = models.BooleanField(
        default=False,
        help_text=_("If hsts_max_age > 0, set the preload flag with the HSTS header"),
    )

    objects = DomainQueryset.as_manager()

    class Meta:
        ordering = ("-canonical", "-machine", "domain")

    def __str__(self):
        return "{domain} pointed at {project}".format(
            domain=self.domain,
            project=self.project.name,
        )

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
        return f"HttpHeader: {self.name} on {self.domain.domain}"


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
    MKDOCS_THEME_RTD = "mkdocs_theme_rtd"
    API_LARGE_DATA = "api_large_data"
    CONDA_APPEND_CORE_REQUIREMENTS = "conda_append_core_requirements"
    ALL_VERSIONS_IN_HTML_CONTEXT = "all_versions_in_html_context"
    RECORD_404_PAGE_VIEWS = "record_404_page_views"
    DISABLE_PAGEVIEWS = "disable_pageviews"
    RESOLVE_PROJECT_FROM_HEADER = "resolve_project_from_header"
    USE_PROXIED_APIS_WITH_PREFIX = "use_proxied_apis_with_prefix"
    ALLOW_VERSION_WARNING_BANNER = "allow_version_warning_banner"

    # Versions sync related features
    SKIP_SYNC_TAGS = "skip_sync_tags"
    SKIP_SYNC_BRANCHES = "skip_sync_branches"
    SKIP_SYNC_VERSIONS = "skip_sync_versions"

    # Dependencies related features
    PIP_ALWAYS_UPGRADE = "pip_always_upgrade"
    USE_NEW_PIP_RESOLVER = "use_new_pip_resolver"
    DONT_INSTALL_LATEST_PIP = "dont_install_latest_pip"
    USE_SPHINX_RTD_EXT_LATEST = "rtd_sphinx_ext_latest"
    INSTALL_LATEST_CORE_REQUIREMENTS = "install_latest_core_requirements"

    # Search related features
    DISABLE_SERVER_SIDE_SEARCH = "disable_server_side_search"
    ENABLE_MKDOCS_SERVER_SIDE_SEARCH = "enable_mkdocs_server_side_search"
    DEFAULT_TO_FUZZY_SEARCH = "default_to_fuzzy_search"

    # Build related features
    SCALE_IN_PROTECTION = "scale_in_prtection"

    FEATURES = (
        (
            MKDOCS_THEME_RTD,
            _("MkDocs: Use Read the Docs theme for MkDocs as default theme"),
        ),
        (
            API_LARGE_DATA,
            _("Build: Try alternative method of posting large data"),
        ),
        (
            CONDA_APPEND_CORE_REQUIREMENTS,
            _("Conda: Append Read the Docs core requirements to environment.yml file"),
        ),
        (
            ALL_VERSIONS_IN_HTML_CONTEXT,
            _(
                "Sphinx: Pass all versions (including private) into the html context "
                "when building with Sphinx"
            ),
        ),
        (
            RECORD_404_PAGE_VIEWS,
            _("Proxito: Record 404s page views."),
        ),
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
        (USE_NEW_PIP_RESOLVER, _("Build: Use new pip resolver")),
        (
            DONT_INSTALL_LATEST_PIP,
            _("Build: Don't install the latest version of pip"),
        ),
        (
            USE_SPHINX_RTD_EXT_LATEST,
            _("Sphinx: Use latest version of the Read the Docs Sphinx extension"),
        ),
        (
            INSTALL_LATEST_CORE_REQUIREMENTS,
            _(
                "Build: Install all the latest versions of Read the Docs core requirements"
            ),
        ),
        # Search related features.
        (
            DISABLE_SERVER_SIDE_SEARCH,
            _("Search: Disable server side search"),
        ),
        (
            ENABLE_MKDOCS_SERVER_SIDE_SEARCH,
            _("Search: Enable server side search for MkDocs projects"),
        ),
        (
            DEFAULT_TO_FUZZY_SEARCH,
            _("Search: Default to fuzzy search for simple search queries"),
        ),
        # Build related features.
        (
            SCALE_IN_PROTECTION,
            _("Build: Set scale-in protection before/after building."),
        ),
    )

    FEATURES = sorted(FEATURES, key=lambda l: l[1])

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
        return "{} feature".format(
            self.get_feature_display(),
        )

    def get_feature_display(self):
        """
        Implement display name field for fake ChoiceField.

        Because the field is not a ChoiceField here, we need to manually
        implement this behavior.
        """
        return dict(self.FEATURES).get(self.feature_id, self.feature_id)


class EnvironmentVariable(TimeStampedModel, models.Model):
    name = models.CharField(
        max_length=128,
        help_text=_("Name of the environment variable"),
    )
    value = models.CharField(
        max_length=2048,
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
