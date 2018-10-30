from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.querysets import RelatedProjectQuerySet


@python_2_unicode_compatible
class DomainData(models.Model):

    """
    Information from a project about it's Sphinx domains.

    This captures data about API objects that exist in that codebase.
    """

    project = models.ForeignKey(
        Project,
        related_name='domain_data',
    )
    version = models.ForeignKey(Version, verbose_name=_('Version'),
                                related_name='domain_data')
    modified_date = models.DateTimeField(_('Publication date'), auto_now=True)
    commit = models.CharField(_('Commit'), max_length=255)

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
    objects = RelatedProjectQuerySet.as_manager()

    def __str__(self):
        return f'DomainData [{self.project.slug}:{self.version.slug}] [{self.domain}:{self.type}] {self.name} -> {self.doc_name}#{self.anchor}'
