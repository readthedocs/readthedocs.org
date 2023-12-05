from django.core.exceptions import ValidationError

from readthedocs.redirects.constants import (
    CLEAN_URL_TO_HTML_REDIRECT,
    EXACT_REDIRECT,
    HTML_TO_CLEAN_URL_REDIRECT,
    PAGE_REDIRECT,
)


def validate_redirect(
    *, project, pk, redirect_type, from_url, to_url, error_class=ValidationError
):
    """
    Validation for redirects.

    This is in a separate function so we can use it in the clean method of the model
    (used in forms), and in the Django Rest Framework serializer (used in the API).
    Since DRF doesn't call the clean method of the model.
    """
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
            project.redirects.filter(redirect_type=redirect_type)
            .exclude(pk=pk)
            .exists()
        )
        if redirect_exists:
            raise error_class(
                f"Only one redirect of type `{redirect_type}` is allowed per project."
            )
