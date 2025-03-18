"""Django models for the redirects app."""

import re

import structlog
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from readthedocs.core.resolver import Resolver
from readthedocs.projects.models import Project
from readthedocs.projects.ordering import ProjectItemPositionManager
from readthedocs.redirects.constants import CLEAN_URL_TO_HTML_REDIRECT
from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import HTML_TO_CLEAN_URL_REDIRECT
from readthedocs.redirects.constants import HTTP_STATUS_CHOICES
from readthedocs.redirects.constants import PAGE_REDIRECT
from readthedocs.redirects.constants import TYPE_CHOICES
from readthedocs.redirects.validators import validate_redirect

from .querysets import RedirectQuerySet


log = structlog.get_logger(__name__)


# FIXME: this help_text message should be dynamic since "Absolute path" doesn't
# make sense for "Prefix Redirects" since the from URL is considered after the
# ``/$lang/$version/`` part. Also, there is a feature for the "Exact Redirects"
# that should be mentioned here: the usage of ``*``.
from_url_helptext = _(
    "Absolute path, excluding the domain. Example: <b>/docs/</b>  or <b>/install.html</b>",
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

    # Store the from_url without the ``*`` wildcard for easier and faster querying.
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
        default="",
    )

    position = models.PositiveIntegerField(
        _("Position"),
        default=0,
        help_text=_("Order of execution of the redirect."),
    )

    create_dt = models.DateTimeField(auto_now_add=True)
    update_dt = models.DateTimeField(auto_now=True)

    _position_manager = ProjectItemPositionManager(position_field_name="position")

    objects = RedirectQuerySet.as_manager()

    class Meta:
        verbose_name = _("redirect")
        verbose_name_plural = _("redirects")
        ordering = (
            "position",
            "-update_dt",
        )
        # TODO: add the project, position unique_together constraint once
        # all redirects have a position set.

    def save(self, *args, **kwargs):
        self.from_url_without_rest = None
        if self.redirect_type in [
            CLEAN_URL_TO_HTML_REDIRECT,
            HTML_TO_CLEAN_URL_REDIRECT,
        ]:
            # These redirects don't make use of the ``from_url``/``to_url`` fields.
            self.to_url = ""
            self.from_url = ""
        else:
            self.to_url = self.normalize_to_url(self.to_url)
            self.from_url = self.normalize_from_url(self.from_url)
            if self.from_url.endswith("*"):
                self.from_url_without_rest = self.from_url.removesuffix("*")

        self._position_manager.change_position_before_save(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._position_manager.change_position_after_delete(self)

    def normalize_from_url(self, path):
        """
        Normalize from_url to be used for matching.

        Normalize the path to always start with one slash,
        and end without a slash, so we can match both,
        with and without a trailing slash.
        """
        path = path.rstrip("/")
        path = "/" + path.lstrip("/")
        return path

    def normalize_to_url(self, path):
        """
        Normalize to_url to be used for redirecting.

        Normalize the path to always start with one slash,
        if the path is not an absolute URL.
        Otherwise, return the path as is.
        """
        if re.match("^https?://", path):
            return path
        path = "/" + path.lstrip("/")
        return path

    def clean(self):
        validate_redirect(
            project=self.project,
            pk=self.pk,
            redirect_type=self.redirect_type,
            from_url=self.from_url,
            to_url=self.to_url,
        )

    @property
    def redirects_to_external_domain(self):
        """Check if the redirect is to an external domain."""
        return bool(re.match("^https?://", self.to_url))

    def __str__(self):
        redirect_text = "{type}: {from_to_url}"
        if self.redirect_type in [PAGE_REDIRECT, EXACT_REDIRECT]:
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
        if self.redirect_type in [PAGE_REDIRECT, EXACT_REDIRECT]:
            return "{from_url} -> {to_url}".format(
                from_url=self.from_url,
                to_url=self.to_url,
            )
        return ""

    def get_full_path(self, filename, language=None, version_slug=None, allow_crossdomain=False):
        """
        Return a full path for a given filename.

        This will include version and language information. No protocol/domain
        is returned.
        """
        # Handle explicit http redirects
        if allow_crossdomain and re.match("^https?://", filename):
            return filename

        return Resolver().resolve_path(
            project=self.project,
            language=language,
            version_slug=version_slug,
            filename=filename,
        )

    def get_redirect_path(self, filename, path=None, language=None, version_slug=None):
        """
        Resolve the redirect for the given filename.

        .. note::

           This method doesn't check if the current path matches ``from_url``,
           that should be done before calling this method
           using ``Redirect.objects.get_matching_redirect_with_path``.

        :param filename: The filename being served.
        :param path: The whole path from the request.
        :param language: The language of the project.
        :param version_slug: The slug of the current version.
        """
        method = getattr(
            self,
            "redirect_{type}".format(
                type=self.redirect_type,
            ),
        )
        return method(filename=filename, path=path, language=language, version_slug=version_slug)

    def _redirect_with_wildcard(self, current_path):
        if self.from_url.endswith("*"):
            if self._will_cause_infinite_redirect(current_path):
                log.debug(
                    "Infinite redirect loop detected",
                    redirect=self,
                )
                return None

            splat = current_path[len(self.from_url_without_rest) :]
            to_url = self.to_url.replace(":splat", splat)
            return to_url
        return self.to_url

    def _will_cause_infinite_redirect(self, current_path):
        """
        Check if this redirect will cause an infinite redirect for the given path.

        We detect infinite redirects of the form:

          /dir/* -> /dir/subdir/:splat

        For example, /dir/test.html will redirect to /dir/subdir/test.html,
        and if the file doesn't exist, it will redirect to
        /dir/subdir/subdir/test.html and then to /dir/subdir/subdir/subdir/test.html and so on.

        We do this by checking if we will redirect to a subdirectory of the current path,
        and if the current path already starts with the path we will redirect to.
        """
        if self.from_url.endswith("*") and ":splat" in self.to_url:
            to_url_without_splat = self.to_url.split(":splat", maxsplit=1)[0]

            redirects_to_subpath = to_url_without_splat.startswith(self.from_url_without_rest)
            if redirects_to_subpath and current_path.startswith(to_url_without_splat):
                return True

        return False

    def redirect_page(self, filename, path, language=None, version_slug=None):
        log.debug("Redirecting...", redirect=self)
        to_url = self._redirect_with_wildcard(current_path=filename)
        if to_url:
            return self.get_full_path(
                filename=to_url,
                language=language,
                version_slug=version_slug,
                allow_crossdomain=True,
            )
        return None

    def redirect_exact(self, filename, path, language=None, version_slug=None):
        log.debug("Redirecting...", redirect=self)
        return self._redirect_with_wildcard(current_path=path)

    def redirect_clean_url_to_html(self, filename, path, language=None, version_slug=None):
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

    def redirect_html_to_clean_url(self, filename, path, language=None, version_slug=None):
        log.debug("Redirecting...", redirect=self)
        to = filename.removesuffix(".html") + "/"
        return self.get_full_path(
            filename=to,
            language=language,
            version_slug=version_slug,
            allow_crossdomain=False,
        )
