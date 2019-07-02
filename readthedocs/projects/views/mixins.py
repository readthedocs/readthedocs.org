# -*- coding: utf-8 -*-

"""Mixin classes for project views."""

from celery import chain
from django.shortcuts import get_object_or_404

from readthedocs.core.utils import prepare_build
from readthedocs.projects.models import Project
from readthedocs.projects.signals import project_import


class ProjectRelationMixin:

    """
    Mixin class for constructing model views for project dashboard.

    This mixin class is used for model views on models that have a relation
    to the :py:class:`Project` model.

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
            slug=self.kwargs[self.project_lookup_url_kwarg],
        )

    def get_queryset(self):
        return self.model.objects.filter(
            **{self.project_lookup_field: self.get_project()}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.project_context_object_name] = self.get_project()
        return context


class ProjectImportMixin:

    """Helpers to import a Project."""

    def import_project(self, project, tags, request):
        """
        Import a Project into Read the Docs.

        - Add the user from request as maintainer
        - Set all the tags to the project
        - Send Django Signal
        - Trigger initial build
        """
        project.users.add(request.user)
        for tag in tags:
            project.tags.add(tag)

        # TODO: this signal could be removed, or used for sync task
        project_import.send(sender=project, request=request)

        self.trigger_initial_build(project, request.user)

    def trigger_initial_build(self, project, user):
        """
        Trigger initial build after project is imported.

        :param project: project's documentation to be built
        :returns: Celery AsyncResult promise
        """

        update_docs, build = prepare_build(project)
        if (update_docs, build) == (None, None):
            return None

        from readthedocs.oauth.tasks import attach_webhook
        task_promise = chain(
            attach_webhook.si(project.pk, user.pk),
            update_docs,
        )
        async_result = task_promise.apply_async()
        return async_result
