from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from readthedocs.subscriptions.constants import TYPE_CNAME
from readthedocs.subscriptions.products import get_feature


def check_domains_limit(project, error_class=ValidationError):
    """Check if the project has reached the limit on the number of domains."""
    feature = get_feature(project, TYPE_CNAME)
    if feature.unlimited:
        return

    if project.domains.count() >= feature.value:
        msg = _(
            f"This project has reached the limit of {feature.value} domains."
            " Consider removing unused domains."
        )
        if settings.ALLOW_PRIVATE_REPOS:
            msg = _(
                f"Your organization has reached the limit of {feature.value} domains."
                " Consider removing unused domains or upgrading your plan."
            )
        raise error_class(msg)
