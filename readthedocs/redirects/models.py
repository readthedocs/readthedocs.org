"""Django models for the redirects app."""

import re

import structlog
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from readthedocs.core.resolver import resolve_path
from readthedocs.projects.models import Project

from .querysets import RedirectQuerySet
from readthedocs.redirects.constants import TYPE_CHOICES, HTTP_STATUS_CHOICES, PAGE_REDIRECT, EXACT_REDIRECT

log = structlog.get_logger(__name__)


# FIXME: this help_text message should be dynamic since "Absolute path" doesn't
# make sense for "Prefix Redirects" since the from URL is considered after the
# ``/$lang/$version/`` part. Also, there is a feature for the "Exact Redirects"
# that should be mentioned here: the usage of ``*``.
from_url_helptext = _(
    "Absolute path, excluding the domain. "
    "Example: <b>/docs/</b>  or <b>/install.html</b>",
)
to_url_helptext = _(
    "Absolute or relative URL. Example: <b>/tutorial/install.html</b>",
)
redirect_type_helptext = _("The type of redirect you wish to use.")


class Redirect(models.Model):

    """A HTTP redirect associated with a Project."""

    project = models.ForeignKey(
        Project,
        verbose_name=_("Project"),
        related_name="redirects",
        on_delete=models.CASCADE,
    )

    redirect_type = models.CharField(
        _("Redirect Type"),
        max_length=255,
        choices=TYPE_CHOICES,
        help_text=redirect_type_helptext,
    )

    from_url = models.CharField(
        _("From URL"),
        max_length=255,
        db_index=True,
        help_text=from_url_helptext,
        blank=True,
    )

    # Store the from_url without the ``*`` wildcard in it for easier and faster querying.
    from_url_without_rest = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Only for internal querying use",
        blank=True,
        null=True,
    )

    to_url = models.CharField(
        _("To URL"),
        max_length=255,
        db_index=True,
        help_text=to_url_helptext,
        blank=True,
    )

    force = models.BooleanField(
        _("Force redirect"),
        null=True,
        default=False,
        help_text=_("Apply the redirect even if the page exists."),
    )

    http_status = models.SmallIntegerField(
        _("HTTP status code"),
        choices=HTTP_STATUS_CHOICES,
        default=302,
    )

    enabled = models.BooleanField(
        _("Enabled"),
        default=True,
        null=True,
        help_text=_("Enable or disable the redirect."),
    )

    description = models.CharField(
        _("Description"),
        blank=True,
        null=True,
        max_length=255,
    )

    # TODO: remove this field and use `enabled` instead.
    status = models.BooleanField(choices=[], default=True, null=True)

    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    objects = RedirectQuerySet.as_manager()

    class Meta:
        verbose_name = _("redirect")
        verbose_name_plural = _("redirects")
        ordering = ("-update_dt",)

    def save(self, *args, **kwargs):
        self.from_url = self.normalize_path(self.from_url)
        self.from_url_without_rest = None
        if self.redirect_type in [
            PAGE_REDIRECT,
            EXACT_REDIRECT,
        ] and self.from_url.endswith("*"):
            self.from_url_without_rest = self.from_url.removesuffix("*")
        super().save(*args, **kwargs)

    def normalize_path(self, path):
        """Normalize a path to be used for matching."""
        path = "/" + path.lstrip("/")
        path = path.rstrip("/")
        return path

    def __str__(self):
        redirect_text = "{type}: {from_to_url}"
        if self.redirect_type in ["prefix", "page", "exact"]:
            return redirect_text.format(
                type=self.get_redirect_type_display(),
                from_to_url=self.get_from_to_url_display(),
            )
        return gettext(
            "Redirect: {}".format(
                self.get_redirect_type_display(),
            ),
        )

    def get_from_to_url_display(self):
        if self.redirect_type in ["prefix", "page", "exact"]:
            from_url = self.from_url
            to_url = self.to_url
            if self.redirect_type == "prefix":
                to_url = "/{lang}/{version}/".format(
                    lang=self.project.language,
                    version=self.project.default_version,
                )
            return "{from_url} -> {to_url}".format(
                from_url=from_url,
                to_url=to_url,
            )
        return ""

    def get_full_path(
        self, filename, language=None, version_slug=None, allow_crossdomain=False
    ):
        """
        Return a full path for a given filename.

        This will include version and language information. No protocol/domain
        is returned.
        """
        # Handle explicit http redirects
        if allow_crossdomain and re.match("^https?://", filename):
            return filename

        return resolve_path(
            project=self.project,
            language=language,
            version_slug=version_slug,
            filename=filename,
        )

    def get_redirect_path(self, filename, path=None, language=None, version_slug=None):
        method = getattr(
            self,
            "redirect_{type}".format(
                type=self.redirect_type,
            ),
        )
        return method(
            filename=filename, path=path, language=language, version_slug=version_slug
        )

    def redirect_page(self, filename, path, language=None, version_slug=None):
        log.debug("Redirecting...", redirect=self)
        to = self.to_url
        if self.from_url.endswith("*"):
            splat = filename[len(self.from_url_without_rest) - 1 :]
            to = to.replace(":splat", splat)
        return self.get_full_path(
            filename=to,
            language=language,
            version_slug=version_slug,
            allow_crossdomain=True,
        )

    def redirect_exact(self, filename, path, language=None, version_slug=None):
        log.debug("Redirecting...", redirect=self)
        if self.from_url.endswith("*"):
            splat = path[len(self.from_url_without_rest) - 1 :]
            to = self.to_url.replace(":splat", splat)
            return to
        return self.to_url

    def redirect_clean_url_to_html(
        self, filename, path, language=None, version_slug=None
    ):
        log.debug("Redirecting...", redirect=self)
        suffixes = ["/", "/index.html"]
        for suffix in suffixes:
            if filename.endswith(suffix):
                to = filename[: -len(suffix)]
                if not to:
                    to = "index.html"
                else:
                    to += ".html"
                return self.get_full_path(
                    filename=to,
                    language=language,
                    version_slug=version_slug,
                    allow_crossdomain=False,
                )

    def redirect_html_to_clean_url(
        self, filename, path, language=None, version_slug=None
    ):
        log.debug("Redirecting...", redirect=self)
        to = filename.removesuffix(".html") + "/"
        return self.get_full_path(
            filename=to,
            language=language,
            version_slug=version_slug,
            allow_crossdomain=False,
        )
