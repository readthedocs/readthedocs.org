"""Mix-in classes for project views."""

from functools import lru_cache

import structlog
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


class ProjectOnboardMixin:
    """Add project onboard context data to project object views."""

    def get_context_data(self, **kwargs):
        """Add onboard context data."""
        context = super().get_context_data(**kwargs)
        # If more than 1 project, don't show onboarding at all. This could
        # change in the future, to onboard each user maybe?
        if Project.objects.for_admin_user(self.request.user).count() > 1:
            return context

        onboard = {}
        project = self.get_object()

        # Show for the first few builds, return last build state
        if project.builds.count() <= 5:
            onboard["build"] = project.latest_internal_build
            if "github" in project.repo:
                onboard["provider"] = "github"
            elif "bitbucket" in project.repo:
                onboard["provider"] = "bitbucket"
            elif "gitlab" in project.repo:
                onboard["provider"] = "gitlab"
            context["onboard"] = onboard

        return context


# Mixins
class ProjectAdminMixin(SuccessMessageMixin):
    """
    Mixin class that provides project sublevel objects.

    This mixin uses several class level variables

    project_url_field
        The URL kwarg name for the project slug

    success_message
        Message when the form is successfully saved, comes from SuccessMessageMixin
    """

    project_url_field = "project_slug"

    def get_queryset(self):
        self.project = self.get_project()
        return self.model.objects.filter(project=self.project)

    @lru_cache(maxsize=1)
    def get_project(self):
        """Return project determined by url kwarg."""
        if self.project_url_field not in self.kwargs:
            return None
        return get_object_or_404(
            Project.objects.for_admin_user(user=self.request.user),
            slug=self.kwargs[self.project_url_field],
        )

    def get_context_data(self, **kwargs):
        """Add project to context data."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        context["superproject"] = project and project.superproject
        return context

    def get_form_kwargs(self):
        kwargs = {
            "project": self.get_project(),
        }
        return kwargs

    def get_form(self, data=None, files=None, **kwargs):
        """Pass in project to form class instance."""
        kwargs.update(self.get_form_kwargs())
        return self.form_class(data, files, **kwargs)


class ProjectSpamMixin:
    """
    Protects views for spammy projects.

    It shows a ``Project marked as spam`` page and return 410 GONE if the
    project's dashboard is denied.
    """

    def is_show_dashboard_denied_wrapper(self):
        """
        Determine if the project has reached dashboard denied treshold.

        This function is wrapped just for testing purposes,
        so we are able to mock it from outside.
        """
        if "readthedocsext.spamfighting" in settings.INSTALLED_APPS:
            from readthedocsext.spamfighting.utils import (  # noqa
                is_show_dashboard_denied,
            )

            if is_show_dashboard_denied(self.get_project()):
                return True
        return False

    def get(self, request, *args, **kwargs):
        if self.is_show_dashboard_denied_wrapper():
            template_name = "errors/dashboard/spam.html"
            return render(request, template_name=template_name, status=410)

        return super().get(request, *args, **kwargs)
