"""Mixin classes for project views"""

from __future__ import absolute_import
from builtins import object
from django.shortcuts import get_object_or_404

from readthedocs.projects.models import Project


class ProjectRelationMixin(object):

    """Mixin class for constructing model views for project dashboard

    This mixin class is used for model views on models that have a relation
    to the :py:cls:`Project` model.

    :cvar project_lookup_url_kwarg: URL kwarg to use in project lookup
    :cvar project_lookup_field: Query field for project relation
    :cvar project_context_object_name: Context object name for project
    """

    project_lookup_url_kwarg = 'project_slug'
    project_lookup_field = 'project'
    project_context_object_name = 'project'

    def get_project_queryset(self):
        return Project.objects.for_admin_user(user=self.request.user)

    def get_project(self):
        if self.project_lookup_url_kwarg not in self.kwargs:
            return None
        return get_object_or_404(
            self.get_project_queryset(),
            slug=self.kwargs[self.project_lookup_url_kwarg]
        )

    def get_queryset(self):
        return self.model.objects.filter(
            **{self.project_lookup_field: self.get_project()}
        )

    def get_context_data(self, **kwargs):
        context = super(ProjectRelationMixin, self).get_context_data(**kwargs)
        context[self.project_context_object_name] = self.get_project()
        return context
