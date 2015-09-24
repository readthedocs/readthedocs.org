import logging

from django import forms

from readthedocs.builds.models import VersionAlias, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import clear_artifacts


log = logging.getLogger(__name__)


class AliasForm(forms.ModelForm):

    class Meta:
        model = VersionAlias
        fields = (
            'project',
            'from_slug',
            'to_slug',
            'largest',
        )

    def __init__(self, instance=None, *args, **kwargs):
        super(AliasForm, self).__init__(instance=instance, *args, **kwargs)
        if instance:
            self.fields['project'].queryset = (Project.objects
                                               .filter(pk=instance.project.pk))


class VersionForm(forms.ModelForm):

    class Meta:
        model = Version
        fields = ['active', 'privacy_level', 'tags']

    def save(self, *args, **kwargs):
        obj = super(VersionForm, self).save(*args, **kwargs)
        if obj.active and not obj.built and not obj.uploaded:
            trigger_build(project=obj.project, version=obj)

    def clean(self):
        cleaned_data = super(VersionForm, self).clean()
        if self.instance.pk is not None:  # new instance only
            if self.instance.active is True and cleaned_data['active'] is False:
                log.info('Removing files for version %s' % self.instance.slug)
                clear_artifacts.delay(version_pk=[self.instance.pk])
        return cleaned_data
