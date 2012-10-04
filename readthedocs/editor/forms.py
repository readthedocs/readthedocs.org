from django import forms
from django.utils.translation import ugettext_lazy as _


class FileForm(forms.Form):
    body = forms.CharField(label=_('Body'), widget=forms.Textarea())
    comment = forms.CharField(label=_('Comment'), widget=forms.Textarea())


class PullRequestForm(forms.Form):
    title = forms.CharField(label=_('Title'))
    comment = forms.CharField(label=_('Comment'), widget=forms.Textarea())
