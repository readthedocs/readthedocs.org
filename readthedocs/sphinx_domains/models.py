"""
Sphinx Domain modeling.

http://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from readthedocs.builds.models import Version
from readthedocs.core.resolver import resolve
from readthedocs.projects.models import Project, HTMLFile
from readthedocs.projects.querysets import RelatedProjectQuerySet


class SphinxDomain(TimeStampedModel):

    """
    Information from a project about it's Sphinx domains.

    This captures data about API objects that exist in that codebase.
    """

    project = models.ForeignKey(
        Project,
        related_name='sphinx_domains',
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        Version,
        verbose_name=_('Version'),
        related_name='sphinx_domains',
        on_delete=models.CASCADE,
    )
    html_file = models.ForeignKey(
        HTMLFile,
        related_name='sphinx_domains',
        null=True,
        on_delete=models.CASCADE,
    )
    commit = models.CharField(_('Commit'), max_length=255, null=True)
    build = models.IntegerField(_('Build id'), null=True)

    domain = models.CharField(
        _('Domain'),
        max_length=255,
    )
    name = models.CharField(
        _('Name'),
        max_length=4092,
    )
    display_name = models.CharField(
        _('Display Name'),
        max_length=4092,
    )
    type = models.CharField(
        _('Type'),
        max_length=255,
    )
    type_display = models.CharField(
        _('Type Display'),
        max_length=4092,
        null=True,
    )
    doc_name = models.CharField(
        _('Doc Name'),
        max_length=4092,
    )
    doc_display = models.CharField(
        _('Doc Display'),
        max_length=4092,
        null=True,
    )
    anchor = models.CharField(
        _('Anchor'),
        max_length=4092,
    )
    objects = RelatedProjectQuerySet.as_manager()

    def __str__(self):
        ret = f'''
            SphinxDomain [{self.project.slug}:{self.version.slug}]
            [{self.domain}:{self.type}] {self.name} ->
            {self.doc_name}
        '''.strip()
        if self.anchor:
            ret += f'#{self.anchor}'
        return ret

    @property
    def role_name(self):
        return f'{self.domain}:{self.type}'

    @property
    def docs_url(self):
        path = self.doc_name
        if self.anchor:
            path += f'#{self.anchor}'
        full_url = resolve(
            project=self.project,
            version_slug=self.version.slug,
            filename=path,
        )
        return full_url
