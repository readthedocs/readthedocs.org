from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_api_key.models import AbstractAPIKey

from readthedocs.projects.models import Project

class BuildAPIKey(AbstractAPIKey):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="build_api_keys",
        help_text=_("Project that this API key grants access to"),
    )

    class Meta(AbstractAPIKey.Meta):
        verbose_name = _("Build API key")
        verbose_name_plural = _("Build API keys")
