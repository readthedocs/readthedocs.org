"""Mixin classes for project views."""

from urllib.parse import urlparse

import structlog
from celery import chain
from django.shortcuts import get_object_or_404

from readthedocs.core.resolver import Resolver
from readthedocs.core.utils import prepare_build
from readthedocs.projects.models import Project
from readthedocs.projects.signals import project_import


log = structlog.get_logger(__name__)


class ProjectRelationMixin:
    """
    Mixin class for constructing model views for project dashboard.

    This mixin class is used for model views on models that have a relation
    to the :py:class:`Project` model.

    :cvar project_lookup_url_kwarg: URL kwarg to use in project lookup
    :cvar project_lookup_field: Query field for project relation
    :cvar project_context_object_name: Context object name for project
    """

    project_lookup_url_kwarg = "project_slug"
    project_lookup_field = "project"
    project_context_object_name = "project"

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
        return self.model.objects.filter(**{self.project_lookup_field: self.get_project()})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.project_context_object_name] = self.get_project()
        return context


class ProjectRelationListMixin:
    """Injects ``subprojects_and_urls`` into the context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subprojects_and_urls"] = self._get_subprojects_and_urls()
        return context

    def _get_subprojects_and_urls(self):
        """
        Get a tuple of subprojects and its absolute URls.

        All subprojects share the domain from the parent,
        so instead of resolving the domain and path for each subproject,
        we resolve only the path of each one.
        """
        subprojects_and_urls = []

        project = self.get_project()
        subprojects = project.subprojects.select_related("child")

        if not subprojects.exists():
            return subprojects_and_urls

        resolver = Resolver()
        main_domain = resolver.get_domain(project)
        parsed_main_domain = urlparse(main_domain)

        for subproject in subprojects:
            subproject_path = resolver.resolve_path(subproject.child)
            parsed_subproject_domain = parsed_main_domain._replace(
                path=subproject_path,
            )
            subprojects_and_urls.append(
                (
                    subproject,
                    parsed_subproject_domain.geturl(),
                )
            )
        return subprojects_and_urls


class ProjectImportMixin:
    """Helpers to import a Project."""

    def finish_import_project(self, request, project):
        """
        Perform last steps to import a project into Read the Docs.

        - Add the user from request as maintainer
        - Send Django Signal
        - Trigger initial build

        It requires the Project was already saved into the DB.

        :param request: Django Request object
        :param project: Project instance just imported (already saved)
        :param tags: tags to add to the project
        """
        project.users.add(request.user)
        log.info(
            "Project imported.",
            project_slug=project.slug,
            user_username=request.user.username,
        )

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
            attach_webhook.si(project.pk),
            update_docs,
        )
        async_result = task_promise.apply_async()
        return async_result
