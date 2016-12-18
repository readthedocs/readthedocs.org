from django import forms

from readthedocs.builds.models import VersionAlias, Version
from readthedocs.projects.models import Project
from readthedocs.core.utils import trigger_build


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
        return obj
