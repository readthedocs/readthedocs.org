from django.db import models

from readthedocs.builds.constants import PULL_REQUEST
from readthedocs.core.utils.extend import (
    get_override_class,
    SettingsOverrideObject
)
from readthedocs.projects.querysets import HTMLFileQuerySet


class HTMLFileManagerBase(models.Manager):

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        queryset_class = get_override_class(
            HTMLFileQuerySet,
            HTMLFileQuerySet._default_class,  # pylint: disable=protected-access
        )
        return super().from_queryset(queryset_class, class_name)

    def get_queryset(self):
        return super().get_queryset().filter(name__endswith='.html')


class HTMLFileManager(SettingsOverrideObject):
    _default_class = HTMLFileManagerBase

