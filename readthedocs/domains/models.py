from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from readthedocs.projects.models import Project


@python_2_unicode_compatible
class DomainData(models.Model):

    """
    Information from a project about it's Sphinx domains.

    This captures data about API objects that exist in that codebase.
    """

    project = models.OneToOneField(
        Project,
        on_delete=models.SET_NULL,
        related_name='domain_data',
        null=True,
        blank=True,
    )
    domain = models.CharField(
        _('Domain'),
        max_length=255,
    )
    name = models.CharField(
        _('Name'),
        max_length=255,
    )
    display_name = models.CharField(
        _('Display Name'),
        max_length=255,
    )
    type = models.CharField(
        _('Type'),
        max_length=255,
    )
    doc_name = models.CharField(
        _('Doc Name'),
        max_length=255,
    )
    anchor = models.CharField(
        _('Anchor'),
        max_length=255,
    )
    priority = models.IntegerField(
        _('Priority'),
    )
