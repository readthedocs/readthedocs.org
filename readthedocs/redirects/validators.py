from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from readthedocs.redirects.constants import CLEAN_URL_TO_HTML_REDIRECT
from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import HTML_TO_CLEAN_URL_REDIRECT
from readthedocs.redirects.constants import PAGE_REDIRECT
from readthedocs.subscriptions.constants import TYPE_REDIRECTS_LIMIT
from readthedocs.subscriptions.products import get_feature


def validate_redirect(*, project, pk, redirect_type, from_url, to_url, error_class=ValidationError):
    """
    Validations for redirects.

    This is in a separate function so we can use it in the clean method of the model
    (used in forms), and in the Django Rest Framework serializer (used in the API).
    Since DRF doesn't call the clean method of the model.
    """
    # Check for the limit if we are creating a new redirect.
    if not pk:
        _check_redirects_limit(project, error_class)

    if redirect_type in [EXACT_REDIRECT, PAGE_REDIRECT]:
        if from_url.endswith("$rest"):
            raise error_class("The $rest wildcard has been removed in favor of *.")
        if "*" in from_url and not from_url.endswith("*"):
            raise error_class("The * wildcard must be at the end of the path.")
        if ":splat" in to_url and not from_url.endswith("*"):
            raise error_class(
                "The * wildcard must be at the end of from_url to use the :splat placeholder in to_url."
            )

    if redirect_type in [CLEAN_URL_TO_HTML_REDIRECT, HTML_TO_CLEAN_URL_REDIRECT]:
        redirect_exists = (
            project.redirects.filter(redirect_type=redirect_type).exclude(pk=pk).exists()
        )
        if redirect_exists:
            raise error_class(
                f"Only one redirect of type `{redirect_type}` is allowed per project."
            )


def _check_redirects_limit(project, error_class):
    """Check if the project has reached the limit on the number of redirects."""
    feature = get_feature(project, TYPE_REDIRECTS_LIMIT)
    if feature.unlimited:
        return

    if project.redirects.count() >= feature.value:
        msg = _(
            f"This project has reached the limit of {feature.value} redirects."
            " Consider replacing some of your redirects with a wildcard redirect."
        )
        if settings.ALLOW_PRIVATE_REPOS:
            msg = _(
                f"This project has reached the limit of {feature.value} redirects."
                " Consider replacing some of your redirects with a wildcard redirect,"
                " or upgrade your plan."
            )
        raise error_class(msg)
