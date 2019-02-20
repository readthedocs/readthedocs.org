"""
Sphinx Domain modeling.

http://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from readthedocs.builds.models import Version
from readthedocs.core.resolver import resolve
from readthedocs.projects.models import Project
from readthedocs.projects.querysets import RelatedProjectQuerySet


class DomainData(TimeStampedModel):

    """
    Information from a project about it's Sphinx domains.

    This captures data about API objects that exist in that codebase.
    """

    project = models.ForeignKey(
        Project,
        related_name='domain_data',
    )
    version = models.ForeignKey(
        Version,
        verbose_name=_('Version'),
        related_name='domain_data',
    )
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
        return f'''
            DomainData [{self.project.slug}:{self.version.slug}]
            [{self.domain}:{self.type}] {self.name} -> {self.doc_name}#{self.anchor}
        '''

    @property
    def doc_type(self):
        return f'{self.domain}:{self.type}'

    @property
    def doc_url(self):
        path = self.doc_name
        if self.anchor:
            path += f'#{self.anchor}'
        full_url = resolve(
            project=self.project,
            version_slug=self.version.slug,
            filename=path,
        )
        return full_url
