from django import forms

from builds.models import VersionAlias, Version
from projects.models import Project


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
