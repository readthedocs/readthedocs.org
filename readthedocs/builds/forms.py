from django import forms

from builds.models import VersionAlias, Version
from projects.models import Project
from core.utils import trigger_build


class AliasForm(forms.ModelForm):

    class Meta:
        model = VersionAlias

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
        super(VersionForm, self).save(*args, **kwargs)
        if self.active and not self.built and not self.uploaded:
            trigger_build(project=self.version.project, version=self.version)
