"""Models for the builds app."""

import datetime
import os.path
import re
from functools import partial

import regex
import structlog
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from polymorphic.models import PolymorphicModel

import readthedocs.builds.automation_actions as actions
from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import BUILD_STATE_TRIGGERED
from readthedocs.builds.constants import BUILD_STATUS_CHOICES
from readthedocs.builds.constants import BUILD_TYPES
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import EXTERNAL_VERSION_STATES
from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.constants import LATEST
from readthedocs.builds.constants import PREDEFINED_MATCH_ARGS
from readthedocs.builds.constants import PREDEFINED_MATCH_ARGS_VALUES
from readthedocs.builds.constants import STABLE
from readthedocs.builds.constants import VERSION_TYPES
from readthedocs.builds.managers import AutomationRuleMatchManager
from readthedocs.builds.managers import ExternalBuildManager
from readthedocs.builds.managers import ExternalVersionManager
from readthedocs.builds.managers import InternalBuildManager
from readthedocs.builds.managers import InternalVersionManager
from readthedocs.builds.managers import VersionManager
from readthedocs.builds.querysets import BuildQuerySet
from readthedocs.builds.querysets import RelatedBuildQuerySet
from readthedocs.builds.querysets import VersionQuerySet
from readthedocs.builds.signals import version_changed
from readthedocs.builds.utils import external_version_name
from readthedocs.builds.utils import get_bitbucket_username_repo
from readthedocs.builds.utils import get_github_username_repo
from readthedocs.builds.utils import get_gitlab_username_repo
from readthedocs.builds.utils import get_vcs_url
from readthedocs.builds.version_slug import generate_unique_version_slug
from readthedocs.builds.version_slug import version_slug_validator
from readthedocs.core.utils import extract_valid_attributes_for_model
from readthedocs.core.utils import trigger_build
from readthedocs.notifications.models import Notification
from readthedocs.projects.constants import BITBUCKET_COMMIT_URL
from readthedocs.projects.constants import DOCTYPE_CHOICES
from readthedocs.projects.constants import GITHUB_COMMIT_URL
from readthedocs.projects.constants import GITHUB_PULL_REQUEST_COMMIT_URL
from readthedocs.projects.constants import GITLAB_COMMIT_URL
from readthedocs.projects.constants import GITLAB_MERGE_REQUEST_COMMIT_URL
from readthedocs.projects.constants import MEDIA_TYPES
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.constants import MKDOCS_HTML
from readthedocs.projects.constants import PRIVACY_CHOICES
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.constants import SPHINX
from readthedocs.projects.constants import SPHINX_HTMLDIR
from readthedocs.projects.constants import SPHINX_SINGLEHTML
from readthedocs.projects.models import APIProject
from readthedocs.projects.models import Project
from readthedocs.projects.ordering import ProjectItemPositionManager
from readthedocs.projects.validators import validate_build_config_file
from readthedocs.projects.version_handling import determine_stable_version


log = structlog.get_logger(__name__)


class Version(TimeStampedModel):
    """Version of a ``Project``."""

    project = models.ForeignKey(
        Project,
        verbose_name=_("Project"),
        related_name="versions",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        _("Type"),
        max_length=20,
        choices=VERSION_TYPES,
        default="unknown",
        db_index=True,
    )
    # used by the vcs backend

    #: The identifier is the ID for the revision this is version is for.
    #: This is the commit hash (e.g. in Git).
    #: If the this version is pointing to a branch,
    #: then ``identifier`` will contain the branch name.
    #: `None`/`null` means it will use the VCS default branch.
    identifier = models.CharField(_("Identifier"), max_length=255, null=True, blank=True)

    #: This is the actual name that we got for the commit stored in
    #: ``identifier``. This might be the tag or branch name like ``"v1.0.4"``.
    #: However this might also hold special version names like ``"latest"``
    #: and ``"stable"``.
    verbose_name = models.CharField(_("Verbose Name"), max_length=255)

    #: The slug is the slugified version of ``verbose_name`` that can be used
    #: in the URL to identify this version in a project. It's also used in the
    #: filesystem to determine how the paths for this version are called. It
    #: must not be used for any other identifying purposes.
    slug = models.CharField(
        _("Slug"),
        max_length=255,
        validators=[version_slug_validator],
        db_index=True,
        help_text=_(
            "A unique identifier used in the URL and links for this version. It can contain lowercase letters, numbers, dots, dashes or underscores. It must start with a lowercase letter or a number."
        ),
    )

    # TODO: this field (`supported`) could be removed. It's returned only on
    # the footer API response but I don't think anybody is using this field at
    # all.
    supported = models.BooleanField(_("Supported"), default=True)

    active = models.BooleanField(_("Active"), default=False)
    state = models.CharField(
        _("State"),
        max_length=20,
        choices=EXTERNAL_VERSION_STATES,
        null=True,
        blank=True,
        help_text=_("State of the PR/MR associated to this version."),
    )
    built = models.BooleanField(_("Built"), default=False)

    # TODO: this field (`uploaded`) could be removed. It was used to mark a
    # version as "Manually uploaded" by the core team, but this is not required
    # anymore. Users can use `build.commands` for these cases now.
    uploaded = models.BooleanField(_("Uploaded"), default=False)

    privacy_level = models.CharField(
        _("Privacy Level"),
        max_length=20,
        choices=PRIVACY_CHOICES,
        default=settings.DEFAULT_VERSION_PRIVACY_LEVEL,
        help_text=_("Level of privacy for this Version."),
    )
    hidden = models.BooleanField(
        _("Hidden"),
        default=False,
        help_text=_("Hide this version from the version (flyout) menu and search results?"),
    )
    machine = models.BooleanField(_("Machine Created"), default=False)

    # Whether the latest successful build for this version contains certain media types
    has_pdf = models.BooleanField(_("Has PDF"), default=False)
    has_epub = models.BooleanField(_("Has ePub"), default=False)
    has_htmlzip = models.BooleanField(_("Has HTML Zip"), default=False)

    documentation_type = models.CharField(
        _("Documentation type"),
        max_length=20,
        choices=DOCTYPE_CHOICES,
        default=SPHINX,
        help_text=_("Type of documentation the version was built with."),
    )

    build_data = models.JSONField(
        _("Data generated at build time by the doctool (`readthedocs-build.yaml`)."),
        default=None,
        null=True,
        blank=True,
    )

    addons = models.BooleanField(
        _("Inject new addons js library for this version"),
        null=True,
        blank=True,
        default=False,
    )

    objects = VersionManager.from_queryset(VersionQuerySet)()
    # Only include BRANCH, TAG, UNKNOWN type Versions.
    internal = InternalVersionManager.from_queryset(partial(VersionQuerySet, internal_only=True))()
    # Only include EXTERNAL type Versions.
    external = ExternalVersionManager.from_queryset(partial(VersionQuerySet, external_only=True))()

    class Meta:
        unique_together = [("project", "slug")]
        ordering = ["-verbose_name"]

    def __str__(self):
        return self.verbose_name

    @property
    def is_private(self):
        """
        Check if the version is private (taking external versions into consideration).

        The privacy level of an external version is given by
        the value of ``project.external_builds_privacy_level``.
        """
        if self.is_external:
            return self.project.external_builds_privacy_level == PRIVATE
        return self.privacy_level == PRIVATE

    @property
    def is_public(self):
        """
        Check if the version is public (taking external versions into consideration).

        This is basically ``is_private`` negated,
        ``is_private`` understands both normal and external versions
        """
        return not self.is_private

    @property
    def is_external(self):
        return self.type == EXTERNAL

    @property
    def is_machine_latest(self):
        return self.machine and self.slug == LATEST

    @property
    def explicit_name(self):
        """
        Version name that is explicit about external origins.

        For example, if a version originates from GitHub pull request #4, then
        ``version.explicit_name == "#4 (PR)"``.

        On the other hand, Versions associated with regular RTD builds
        (e.g. new tags or branches), simply return :obj:`~.verbose_name`.
        This means that a regular git tag named **v4** will correspond to
        ``version.explicit_name == "v4"``.
        """
        if not self.is_external:
            return self.verbose_name

        template = "#{name} ({abbrev})"
        external_origin = external_version_name(self)
        abbrev = "".join(word[0].upper() for word in external_origin.split())
        return template.format(name=self.verbose_name, abbrev=abbrev)

    @property
    def external_version_name(self):
        return external_version_name(self)

    @property
    def ref(self):
        """
        The version slug where the ``stable`` version points to.

        It returns None when the version is not stable (machine created).
        """
        if self.slug == STABLE and self.machine:
            stable = determine_stable_version(self.project.versions(manager=INTERNAL).all())
            if stable:
                return stable.slug

    @property
    def vcs_url(self):
        return get_vcs_url(
            project=self.project,
            version_type=self.type,
            version_name=self.git_identifier,
        )

    @property
    def last_build(self):
        # TODO deprecated in favor of `latest_build`, which matches naming on
        # the Project model
        return self.latest_build

    @property
    def latest_build(self):
        return self.builds.order_by("-date").first()

    @property
    def latest_successful_build(self):
        return (
            self.builds.filter(
                state=BUILD_STATE_FINISHED,
                success=True,
            )
            .order_by("-date")
            .first()
        )

    @property
    def config(self):
        """
        Proxy to the configuration of the build.

        :returns: The configuration used in the last successful build.
        :rtype: dict
        """
        last_build = (
            self.builds.filter(
                state=BUILD_STATE_FINISHED,
                success=True,
            )
            .order_by("-date")
            .only("_config")
            .first()
        )
        if last_build:
            return last_build.config
        return None

    @property
    def git_identifier(self):
        """
        Return the branch or tag name of the version.

        The result could be used as ref in a git repo, e.g. for linking to
        GitHub, Bitbucket or GitLab.

        - If the version is latest (machine created), we resolve to the default branch of the project.
        - If the version is stable (machine created), we resolve to the branch that the stable version points to.
        - If the version is external, we return the PR identifier, since we don't have access to the name of the branch.
        """
        # Latest is special as it doesn't contain the actual name in verbose_name,
        # but in the identifier field.
        if self.slug == LATEST and self.machine:
            return self.identifier

        # Stable is special as it doesn't contain the actual name in verbose_name.
        if self.slug == STABLE and self.machine:
            original_stable = self.project.get_original_stable_version()
            # NOTE: we no longer save branch names with the "origin/" prefix,
            # but we remove it for old versions.
            if original_stable:
                return original_stable.verbose_name.removeprefix("origin/")
            return self.identifier.removeprefix("origin/")

        # For all other cases, verbose_name contains the actual name of the branch/tag.
        return self.verbose_name

    def get_absolute_url(self):
        """
        Get the absolute URL to the docs of the version.

        For external versions (PR builds), if the version is not built, we return the
        build detail page since these versions are ephemeral and read-only.

        For internal versions, if not built, we return the project's version dashboard page.

        Because documentation projects can be hosted on separate domains, this function ALWAYS
        returns with a full "http(s)://<domain>/" prefix.
        """
        if not self.built and not self.uploaded:
            # External versions (PR builds) should link to the build detail page
            # since they're read-only and we can't "edit" them
            if self.type == EXTERNAL:
                latest_build = self.latest_build
                if latest_build:
                    return latest_build.get_full_url()

            # For internal versions, fall back to the project version detail page
            # TODO: Stop assuming protocol based on settings.DEBUG
            # (this pattern is also used in builds.tasks for sending emails)
            protocol = "http" if settings.DEBUG else "https"
            return "{}://{}{}".format(
                protocol,
                settings.PRODUCTION_DOMAIN,
                reverse(
                    "project_version_detail",
                    kwargs={
                        "project_slug": self.project.slug,
                        "version_slug": self.slug,
                    },
                ),
            )
        external = self.type == EXTERNAL
        return self.project.get_docs_url(
            version_slug=self.slug,
            external=external,
        )

    def delete(self, *args, **kwargs):
        from readthedocs.projects.tasks.utils import clean_project_resources

        log.info("Removing files for version.", version_slug=self.slug)
        clean_project_resources(self.project, self)
        super().delete(*args, **kwargs)

    def clean_resources(self, version_slug=None):
        """
        Remove all resources from this version.

        This includes:

        - Files from storage
        - Search index
        - Imported files

        :param version_slug: The version slug to use.
         Version resources are stored using the version's slug,
         since slugs can change, we need to be able to provide a different slug
         sometimes to clean old resources.
        """
        from readthedocs.projects.tasks.utils import clean_project_resources

        log.info(
            "Removing files for version.",
            project_slug=self.project.slug,
            version_slug=self.slug,
        )
        clean_project_resources(
            project=self.project,
            version=self,
            version_slug=version_slug,
        )
        self.built = False
        self.save()
        self.purge_cdn(version_slug=version_slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_version_slug(self.verbose_name, self)
        super().save(*args, **kwargs)

    def post_save(self, was_active=False):
        """
        Run extra steps after updating a version.

        This method isn't called automatically by a signal but is called explicitly
        from other processes.

        Useful to run after the version has been saved/updated
        by the user, like from a form or API.

        - When a version is deactivated, we need to clean up its
          files from storage, and search index.
        - When a version is activated, we need to trigger a build.
        - We also need to purge the cache from the CDN,
          since the version could have been activated/deactivated,
          or its privacy level could have changed.
        """
        # If the version is deactivated, we need to clean up the files.
        if was_active and not self.active:
            self.clean_resources()
            return
        # If the version is activated, we need to trigger a build.
        if not was_active and self.active:
            trigger_build(project=self.project, version=self)
        # Purge the cache from the CDN for any other changes.
        self.purge_cdn()

    def purge_cdn(self, version_slug=None):
        """
        Purge the cache from the CDN.

        :param version_slug: The version slug to use.
         Version resources are stored using the version's slug,
         since slugs can change, we need to be able to provide a different slug
         sometimes to clean old resources.
        """
        version_changed.send(sender=self.__class__, version=self, version_slug=version_slug)

    @property
    def identifier_friendly(self):
        """Return display friendly identifier."""
        if not self.identifier:
            # Text shown to user when we don't know yet what's the ``identifier`` for this version.
            # This usually happens when we haven't pulled the ``default_branch`` for LATEST.
            return "Unknown yet"

        if re.match(r"^[0-9a-f]{40}$", self.identifier, re.I):
            return self.identifier[:8]
        return self.identifier

    @property
    def is_editable(self):
        return self.type == BRANCH

    @property
    def is_sphinx_type(self):
        return self.documentation_type in {SPHINX, SPHINX_HTMLDIR, SPHINX_SINGLEHTML}

    @property
    def is_mkdocs_type(self):
        return self.documentation_type in {MKDOCS, MKDOCS_HTML}

    def get_subdomain_url(self):
        external = self.type == EXTERNAL
        return self.project.get_docs_url(
            version_slug=self.slug,
            lang_slug=self.project.language,
            external=external,
        )

    def get_downloads(self, pretty=False, resolver=None):
        project = self.project
        data = {}

        def prettify(k):
            return k if pretty else k.lower()

        if self.has_pdf:
            data[prettify("PDF")] = project.get_production_media_url(
                "pdf",
                self.slug,
                resolver=resolver,
            )

        if self.has_htmlzip:
            data[prettify("HTML")] = project.get_production_media_url(
                "htmlzip",
                self.slug,
                resolver=resolver,
            )
        if self.has_epub:
            data[prettify("Epub")] = project.get_production_media_url(
                "epub",
                self.slug,
                resolver=resolver,
            )
        return data

    def get_conf_py_path(self):
        conf_py_path = self.project.conf_dir(self.slug)
        checkout_prefix = self.project.checkout_path(self.slug)
        conf_py_path = os.path.relpath(conf_py_path, checkout_prefix)
        return conf_py_path

    def get_storage_paths(self, version_slug=None):
        """
        Return a list of all build artifact storage paths for this version.

        :param version_slug: The version slug to use.
         Version resources are stored using the version's slug,
         since slugs can change, we need to be able to provide a different slug
         sometimes to clean old resources.
        :rtype: list
        """
        paths = []

        slug = version_slug or self.slug
        for type_ in MEDIA_TYPES:
            paths.append(
                self.project.get_storage_path(
                    type_=type_,
                    version_slug=slug,
                    include_file=False,
                    version_type=self.type,
                )
            )

        return paths


class APIVersion(Version):
    """
    Version proxy model for API data deserialization.

    This replaces the pattern where API data was deserialized into a mocked
    :py:class:`Version` object.
    This pattern was confusing, as it was not explicit
    as to what form of object you were working with -- API backed or database
    backed.

    This model preserves the Version model methods, allowing for overrides on
    model field differences. This model pattern will generally only be used on
    builder instances, where we are interacting solely with API data.
    """

    project = None
    # This is a property in the original model, in order to
    # be able to assign it a value in the constructor, we need to re-declare it
    # as an attribute here.
    git_identifier = None

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self.project = APIProject(**kwargs.pop("project", {}))
        self.canonical_url = kwargs.pop("canonical_url", None)
        self.git_identifier = kwargs.pop("git_identifier", None)
        # These fields only exist on the API return, not on the model, so we'll
        # remove them to avoid throwing exceptions due to unexpected fields
        for key in ["resource_uri", "absolute_url", "downloads"]:
            try:
                del kwargs[key]
            except KeyError:
                pass
        valid_attributes, invalid_attributes = extract_valid_attributes_for_model(
            model=Version,
            attributes=kwargs,
        )
        if invalid_attributes:
            log.warning(
                "APIVersion got unexpected attributes.",
                invalid_attributes=invalid_attributes,
            )

        super().__init__(*args, **valid_attributes)

    def save(self, *args, **kwargs):
        return 0


class Build(models.Model):
    """Build data."""

    project = models.ForeignKey(
        Project,
        verbose_name=_("Project"),
        related_name="builds",
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        Version,
        verbose_name=_("Version"),
        null=True,
        related_name="builds",
        on_delete=models.SET_NULL,
    )
    type = models.CharField(
        _("Type"),
        max_length=55,
        choices=BUILD_TYPES,
        default="html",
    )

    # Describe build state as where in the build process the build is. This
    # allows us to show progression to the user in the form of a progress bar
    # or in the build listing
    state = models.CharField(
        _("State"),
        max_length=55,
        choices=BUILD_STATE,
        default=BUILD_STATE_TRIGGERED,
        db_index=True,
    )

    # Describe status as *why* the build is in a particular state. It is
    # helpful for communicating more details about state to the user, but it
    # doesn't help describe progression
    # https://github.com/readthedocs/readthedocs.org/pull/7123#issuecomment-635065807
    status = models.CharField(
        _("Status"),
        choices=BUILD_STATUS_CHOICES,
        max_length=32,
        null=True,
        default=None,
        blank=True,
    )
    date = models.DateTimeField(_("Date"), auto_now_add=True, db_index=True)
    healthcheck = models.DateTimeField(_("Healthcheck"), null=True, blank=True)
    success = models.BooleanField(_("Success"), default=True)

    # TODO: remove these fields (setup, setup_error, output, error, exit_code)
    # since they are not used anymore in the new implementation and only really
    # old builds (>5 years ago) only were using these fields.
    setup = models.TextField(_("Setup"), null=True, blank=True)
    setup_error = models.TextField(_("Setup error"), null=True, blank=True)
    output = models.TextField(_("Output"), default="", blank=True)
    error = models.TextField(_("Error"), default="", blank=True)
    exit_code = models.IntegerField(_("Exit code"), null=True, blank=True)

    # Metadata from were the build happened.
    # This is also used after the version is deleted.
    commit = models.CharField(
        _("Commit"),
        max_length=255,
        null=True,
        blank=True,
    )
    version_slug = models.CharField(
        _("Version slug"),
        max_length=255,
        null=True,
        blank=True,
    )
    version_name = models.CharField(
        _("Version name"),
        max_length=255,
        null=True,
        blank=True,
    )
    version_type = models.CharField(
        _("Version type"),
        max_length=32,
        choices=VERSION_TYPES,
        null=True,
        blank=True,
    )
    _config = models.JSONField(
        _("Configuration used in the build"),
        null=True,
        blank=True,
    )
    readthedocs_yaml_path = models.CharField(
        _("Custom build configuration file path used in this build"),
        max_length=1024,
        default=None,
        blank=True,
        null=True,
        validators=[validate_build_config_file],
    )

    length = models.IntegerField(_("Build Length"), null=True, blank=True)

    builder = models.CharField(
        _("Builder"),
        max_length=255,
        null=True,
        blank=True,
    )

    cold_storage = models.BooleanField(
        _("Cold Storage"),
        null=True,
        help_text="Build steps stored outside the database.",
    )

    task_id = models.CharField(
        _("Celery task id"),
        max_length=36,
        null=True,
        blank=True,
    )
    task_executed_at = models.DateTimeField(
        _("Task executed at datetime"),
        null=True,
        blank=True,
    )

    notifications = GenericRelation(
        Notification,
        related_query_name="build",
        content_type_field="attached_to_content_type",
        object_id_field="attached_to_id",
    )

    # Managers
    objects = BuildQuerySet.as_manager()
    # Only include BRANCH, TAG, UNKNOWN type Version builds.
    internal = InternalBuildManager.from_queryset(BuildQuerySet)()
    # Only include EXTERNAL type Version builds.
    external = ExternalBuildManager.from_queryset(BuildQuerySet)()

    CONFIG_KEY = "__config"

    class Meta:
        ordering = ["-date"]
        get_latest_by = "date"
        indexes = [
            models.Index(fields=["project", "date"]),
            models.Index(fields=["version", "date"]),
            # Useful for `/_/addons/` API endpoint.
            # Query: ``version.builds.filter(success=True, state=BUILD_STATE_FINISHED)``
            models.Index(fields=["version", "state", "date", "success"]),
            models.Index(fields=["version", "state", "type"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_changed = False

    @property
    def previous(self):
        """
        Returns the previous build to the current one.

        Matching the project and version.
        """
        date = self.date or timezone.now()
        if self.project is not None and self.version is not None:
            return (
                Build.objects.filter(
                    project=self.project,
                    version=self.version,
                    date__lt=date,
                )
                .order_by("-date")
                .first()
            )
        return None

    @property
    def config(self):
        """
        Get the config used for this build.

        Since we are saving the config into the JSON field only when it differs
        from the previous one, this helper returns the correct JSON used in this
        Build object (it could be stored in this object or one of the previous
        ones).
        """
        # TODO: now that we are using a proper JSONField here, we could
        # probably change this field to be a ForeignKey to avoid repeating the
        # config file over and over again and reuse them to save db data as
        # well
        if self._config and self.CONFIG_KEY in self._config:
            return Build.objects.only("_config").get(pk=self._config[self.CONFIG_KEY])._config
        return self._config

    @config.setter
    def config(self, value):
        """
        Set `_config` to value.

        `_config` should never be set directly from outside the class.
        """
        self._config = value
        self._config_changed = True

    def save(self, *args, **kwargs):  # noqa
        """
        Save object.

        To save space on the db we only save the config if it's different
        from the previous one.

        If the config is the same, we save the pk of the object
        that has the **real** config under the `CONFIG_KEY` key.
        """
        if self.pk is None or self._config_changed:
            previous = self.previous
            if previous is not None and self._config and self._config == previous.config:
                previous_pk = previous._config.get(self.CONFIG_KEY, previous.pk)
                self._config = {self.CONFIG_KEY: previous_pk}

        if self.version:
            self.version_name = self.version.verbose_name
            self.version_slug = self.version.slug
            self.version_type = self.version.type

        super().save(*args, **kwargs)
        self._config_changed = False

    def get_absolute_url(self):
        return reverse("builds_detail", args=[self.project.slug, self.pk])

    def get_full_url(self):
        """
        Get full url of the build including domain.

        Example: https://readthedocs.org/projects/pip/builds/99999999/
        """
        scheme = "http" if settings.DEBUG else "https"
        full_url = "{scheme}://{domain}{absolute_url}".format(
            scheme=scheme,
            domain=settings.PRODUCTION_DOMAIN,
            absolute_url=self.get_absolute_url(),
        )
        return full_url

    def get_version_name(self):
        if self.version:
            return self.version.verbose_name
        return self.version_name

    def get_version_slug(self):
        if self.version:
            return self.version.slug
        return self.version_slug

    def get_version_type(self):
        if self.version:
            return self.version.type
        return self.version_type

    @property
    def vcs_url(self):
        if self.version:
            return self.version.vcs_url
        return get_vcs_url(
            project=self.project,
            version_type=self.get_version_type(),
            version_name=self.get_version_name(),
        )

    def get_commit_url(self):
        """Return the commit URL."""
        repo_url = self.project.repo
        if self.is_external:
            if "github" in repo_url:
                user, repo = get_github_username_repo(repo_url)
                if not user and not repo:
                    return ""

                return GITHUB_PULL_REQUEST_COMMIT_URL.format(
                    user=user,
                    repo=repo,
                    number=self.get_version_name(),
                    commit=self.commit,
                )
            if "gitlab" in repo_url:
                user, repo = get_gitlab_username_repo(repo_url)
                if not user and not repo:
                    return ""

                return GITLAB_MERGE_REQUEST_COMMIT_URL.format(
                    user=user,
                    repo=repo,
                    number=self.get_version_name(),
                    commit=self.commit,
                )
            # TODO: Add External Version Commit URL for Bitbucket.
        else:
            if "github" in repo_url:
                user, repo = get_github_username_repo(repo_url)
                if not user and not repo:
                    return ""

                return GITHUB_COMMIT_URL.format(user=user, repo=repo, commit=self.commit)
            if "gitlab" in repo_url:
                user, repo = get_gitlab_username_repo(repo_url)
                if not user and not repo:
                    return ""

                return GITLAB_COMMIT_URL.format(user=user, repo=repo, commit=self.commit)
            if "bitbucket" in repo_url:
                user, repo = get_bitbucket_username_repo(repo_url)
                if not user and not repo:
                    return ""

                return BITBUCKET_COMMIT_URL.format(user=user, repo=repo, commit=self.commit)

        return None

    @property
    def finished(self):
        """Return if build has an end state."""
        return self.state in BUILD_FINAL_STATES

    @property
    def is_stale(self):
        """Return if build state is triggered & date more than 5m ago."""
        mins_ago = timezone.now() - datetime.timedelta(minutes=5)
        return self.state == BUILD_STATE_TRIGGERED and self.date < mins_ago

    @property
    def is_external(self):
        type = self.version_type
        if self.version:
            type = self.version.type
        return type == EXTERNAL

    @property
    def can_rebuild(self):
        """
        Check if external build can be rebuilt.

        Rebuild can be done only if the build is external,
        build version is active and
        it's the latest build for the version.
        see https://github.com/readthedocs/readthedocs.org/pull/6995#issuecomment-852918969
        """
        if self.is_external:
            is_latest_build = (
                self
                == Build.objects.filter(project=self.project, version=self.version)
                .only("id")
                .first()
            )
            return self.version and self.version.active and is_latest_build
        return False

    @property
    def external_version_name(self):
        return external_version_name(self)

    def reset(self):
        """
        Reset the build so it can be re-used when re-trying.

        Dates and states are usually overridden by the build,
        we care more about deleting the commands.
        """
        self.state = BUILD_STATE_TRIGGERED
        self.status = ""
        self.success = True
        self.output = ""
        self.error = ""
        self.exit_code = None
        self.builder = ""
        self.cold_storage = False
        self.commands.all().delete()
        self.notifications.all().delete()
        self.save()


class BuildCommandResultMixin:
    """
    Mixin for common command result methods/properties.

    Shared methods between the database model :py:class:`BuildCommandResult` and
    non-model representations of build command results from the API
    """

    @property
    def successful(self):
        """Did the command exit with a successful exit code."""
        return self.exit_code == 0

    @property
    def failed(self):
        """
        Did the command exit with a failing exit code.

        Helper for inverse of :py:meth:`successful`
        """
        return not self.successful

    @property
    def finished(self):
        """
        Check if the command has finished running.

        This is determined by checking if the `end_time` is not None.
        """
        return self.end_time is not None


class BuildCommandResult(BuildCommandResultMixin, models.Model):
    """Build command for a ``Build``."""

    build = models.ForeignKey(
        Build,
        verbose_name=_("Build"),
        related_name="commands",
        on_delete=models.CASCADE,
    )

    command = models.TextField(_("Command"))
    description = models.TextField(_("Description"), blank=True)
    output = models.TextField(_("Command output"), blank=True)
    exit_code = models.IntegerField(_("Command exit code"), null=True, blank=True)

    start_time = models.DateTimeField(_("Start time"), null=True, blank=True)
    end_time = models.DateTimeField(_("End time"), null=True, blank=True)

    class Meta:
        ordering = ["start_time"]
        get_latest_by = "start_time"

    objects = RelatedBuildQuerySet.as_manager()

    @property
    def run_time(self):
        """Total command runtime in seconds."""
        if self.start_time is not None and self.end_time is not None:
            diff = self.end_time - self.start_time
            return diff.seconds


class VersionAutomationRule(PolymorphicModel, TimeStampedModel):
    """Versions automation rules for projects."""

    ACTIVATE_VERSION_ACTION = "activate-version"
    DELETE_VERSION_ACTION = "delete-version"
    HIDE_VERSION_ACTION = "hide-version"
    MAKE_VERSION_PUBLIC_ACTION = "make-version-public"
    MAKE_VERSION_PRIVATE_ACTION = "make-version-private"
    SET_DEFAULT_VERSION_ACTION = "set-default-version"

    ACTIONS = (
        (ACTIVATE_VERSION_ACTION, _("Activate version")),
        (HIDE_VERSION_ACTION, _("Hide version")),
        (MAKE_VERSION_PUBLIC_ACTION, _("Make version public")),
        (MAKE_VERSION_PRIVATE_ACTION, _("Make version private")),
        (SET_DEFAULT_VERSION_ACTION, _("Set version as default")),
        (DELETE_VERSION_ACTION, _("Delete version")),
    )

    allowed_actions_on_create = {}
    allowed_actions_on_delete = {}

    project = models.ForeignKey(
        Project,
        related_name="automation_rules",
        on_delete=models.CASCADE,
    )
    priority = models.PositiveIntegerField(
        _("Rule priority"),
        help_text=_("A lower number (0) means a higher priority"),
        default=0,
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        null=True,
        blank=True,
    )
    match_arg = models.CharField(
        _("Match argument"),
        help_text=_("Value used for the rule to match the version"),
        max_length=255,
    )
    predefined_match_arg = models.CharField(
        _("Predefined match argument"),
        help_text=_(
            "Match argument defined by us, it is used if is not None, "
            "otherwise match_arg will be used."
        ),
        max_length=255,
        choices=PREDEFINED_MATCH_ARGS,
        null=True,
        blank=True,
        default=None,
    )
    action = models.CharField(
        _("Action"),
        help_text=_("Action to apply to matching versions"),
        max_length=32,
        choices=ACTIONS,
    )
    action_arg = models.CharField(
        _("Action argument"),
        help_text=_("Value used for the action to perfom an operation"),
        max_length=255,
        null=True,
        blank=True,
    )
    version_type = models.CharField(
        _("Version type"),
        help_text=_("Type of version the rule should be applied to"),
        max_length=32,
        choices=VERSION_TYPES,
    )

    _position_manager = ProjectItemPositionManager(position_field_name="priority")

    class Meta:
        unique_together = (("project", "priority"),)
        ordering = ("priority", "-modified", "-created")

    def get_match_arg(self):
        """Get the match arg defined for `predefined_match_arg` or the match from user."""
        match_arg = PREDEFINED_MATCH_ARGS_VALUES.get(
            self.predefined_match_arg,
        )
        return match_arg or self.match_arg

    def run(self, version, **kwargs):
        """
        Run an action if `version` matches the rule.

        :type version: readthedocs.builds.models.Version
        :returns: True if the action was performed
        """
        if version.type != self.version_type:
            return False

        match, result = self.match(version, self.get_match_arg())
        if match:
            self.apply_action(version, result)
            AutomationRuleMatch.objects.register_match(
                rule=self,
                version=version,
            )
            return True
        return False

    def match(self, version, match_arg):
        """
        Returns True and the match result if the version matches the rule.

        :type version: readthedocs.builds.models.Version
        :param str match_arg: Additional argument to perform the match
        :returns: A tuple of (boolean, match_resul).
                  The result will be passed to `apply_action`.
        """
        return False, None

    def apply_action(self, version, match_result):
        """
        Apply the action from allowed_actions_on_*.

        :type version: readthedocs.builds.models.Version
        :param any match_result: Additional context from the match operation
        :raises: NotImplementedError if the action
                 isn't implemented or supported for this rule.
        """
        action = self.allowed_actions_on_create.get(
            self.action
        ) or self.allowed_actions_on_delete.get(self.action)
        if action is None:
            raise NotImplementedError
        action(version, match_result, self.action_arg)

    def move(self, steps):
        """
        Change the priority of this Automation Rule.

        This is done by moving it ``n`` steps,
        relative to the other priority rules.
        The priority from the other rules are updated too.

        :param steps: Number of steps to be moved
                      (it can be negative)
        """
        total = self.project.automation_rules.count()
        current_priority = self.priority
        new_priority = (current_priority + steps) % total
        self.priority = new_priority
        self.save()

    def save(self, *args, **kwargs):
        """Override method to update the other priorities before save."""
        self._position_manager.change_position_before_save(self)
        if not self.description:
            self.description = self.get_description()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override method to update the other priorities after delete."""
        super().delete(*args, **kwargs)
        self._position_manager.change_position_after_delete(self)

    def get_description(self):
        if self.description:
            return self.description
        return f"{self.get_action_display()}"

    def get_edit_url(self):
        raise NotImplementedError

    def __str__(self):
        class_name = self.__class__.__name__
        return f"({self.priority}) {class_name}/{self.get_action_display()}"


class RegexAutomationRule(VersionAutomationRule):
    TIMEOUT = 1  # timeout in seconds

    allowed_actions_on_create = {
        VersionAutomationRule.ACTIVATE_VERSION_ACTION: actions.activate_version,
        VersionAutomationRule.HIDE_VERSION_ACTION: actions.hide_version,
        VersionAutomationRule.MAKE_VERSION_PUBLIC_ACTION: actions.set_public_privacy_level,
        VersionAutomationRule.MAKE_VERSION_PRIVATE_ACTION: actions.set_private_privacy_level,
        VersionAutomationRule.SET_DEFAULT_VERSION_ACTION: actions.set_default_version,
    }

    allowed_actions_on_delete = {
        VersionAutomationRule.DELETE_VERSION_ACTION: actions.delete_version,
    }

    class Meta:
        proxy = True

    def match(self, version, match_arg):
        """
        Find a match using regex.search.

        .. note::

           We use the regex module with the timeout
           arg to avoid ReDoS.

           We could use a finite state machine type of regex too,
           but there isn't a stable library at the time of writing this code.
        """
        try:
            match = regex.search(
                match_arg,
                version.verbose_name,
                # Compatible with the re module
                flags=regex.VERSION0,
                timeout=self.TIMEOUT,
            )
            return bool(match), match
        except TimeoutError:
            log.warning(
                "Timeout while parsing regex.",
                pattern=match_arg,
                version_slug=version.slug,
            )
        except Exception:
            log.exception("Error parsing regex.", exc_info=True)
        return False, None

    def get_edit_url(self):
        return reverse(
            "projects_automation_rule_regex_edit",
            args=[self.project.slug, self.pk],
        )


class AutomationRuleMatch(TimeStampedModel):
    ACTIONS_PAST_TENSE = {
        VersionAutomationRule.ACTIVATE_VERSION_ACTION: _("Version activated"),
        VersionAutomationRule.HIDE_VERSION_ACTION: _("Version hidden"),
        VersionAutomationRule.MAKE_VERSION_PUBLIC_ACTION: _("Version set to public privacy"),
        VersionAutomationRule.MAKE_VERSION_PRIVATE_ACTION: _("Version set to private privacy"),
        VersionAutomationRule.SET_DEFAULT_VERSION_ACTION: _("Version set as default"),
        VersionAutomationRule.DELETE_VERSION_ACTION: _("Version deleted"),
    }

    rule = models.ForeignKey(
        VersionAutomationRule,
        verbose_name=_("Matched rule"),
        related_name="matches",
        on_delete=models.CASCADE,
    )

    # Metadata from when the match happened.
    version_name = models.CharField(max_length=255)
    match_arg = models.CharField(max_length=255)
    action = models.CharField(
        max_length=255,
        choices=VersionAutomationRule.ACTIONS,
    )
    version_type = models.CharField(
        max_length=32,
        choices=VERSION_TYPES,
    )

    objects = AutomationRuleMatchManager()

    class Meta:
        ordering = ("-modified", "-created")

    def get_action_past_tense(self):
        return self.ACTIONS_PAST_TENSE.get(self.action)
