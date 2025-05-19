"""Gold subscription forms."""

from django import forms
from django.utils.translation import gettext_lazy as _

from readthedocs.projects.models import Project

from .models import LEVEL_CHOICES
from .models import GoldUser


class GoldSubscriptionForm(forms.ModelForm):
    """Gold subscription form."""

    class Meta:
        model = GoldUser
        fields = ["level"]

    level = forms.ChoiceField(
        required=True,
        choices=LEVEL_CHOICES,
    )


class GoldProjectForm(forms.Form):
    """Gold users form to select projects to remove ads from."""

    project = forms.ChoiceField(
        required=True,
        help_text="Select a project.",
    )

    def __init__(self, active_user, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.projects = kwargs.pop("projects", None)
        super().__init__(*args, **kwargs)
        self.fields["project"].choices = self.generate_choices(active_user)

    def generate_choices(self, active_user):
        queryset = Project.objects.filter(users=active_user)
        choices = ((proj.slug, str(proj)) for proj in queryset)
        return choices

    def clean_project(self):
        project_slug = self.cleaned_data.get("project", "")
        project_instance = Project.objects.filter(slug=project_slug)

        if not project_instance.exists():
            raise forms.ValidationError(_("No project found."))
        if project_instance.first() in self.projects:
            raise forms.ValidationError(_("This project is already Ad-Free."))
        return project_slug

    def clean(self):
        cleaned_data = super().clean()
        if self.projects.count() < self.user.num_supported_projects:
            return cleaned_data

        self.add_error(
            None,
            "You already have the max number of supported projects.",
        )
