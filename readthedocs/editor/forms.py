from django import forms


class FileForm(forms.Form):
    body = forms.CharField(label='Body', widget=forms.Textarea())
    comment = forms.CharField(label='Comment', widget=forms.Textarea())


class PullRequestForm(forms.Form):
    title = forms.CharField(label='Title')
    comment = forms.CharField(label='Comment', widget=forms.Textarea())