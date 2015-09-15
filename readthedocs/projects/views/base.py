from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from readthedocs.projects.models import Project


class ProjectOnboardMixin(object):

    '''Add project onboard context data to project object views'''

    def get_context_data(self, **kwargs):
        """Add onboard context data"""
        context = super(ProjectOnboardMixin, self).get_context_data(**kwargs)
        # If more than 1 project, don't show onboarding at all. This could
        # change in the future, to onboard each user maybe?
        if Project.objects.for_admin_user(self.request.user).count() > 1:
            return context

        onboard = {}
        project = self.get_object()

        # Show for the first few builds, return last build state
        if project.builds.count() <= 5:
            onboard['build'] = project.get_latest_build(finished=False)
            if 'github' in project.repo:
                onboard['provider'] = 'github'
            elif 'bitbucket' in project.repo:
                onboard['provider'] = 'bitbucket'
            context['onboard'] = onboard

        return context


# Mixins
class ProjectAdminMixin(object):

    '''Mixin class that provides project sublevel objects

    This mixin uses several class level variables

    project_url_field
        The URL kwarg name for the organization slug

    '''

    project_url_field = 'project'

    def get_queryset(self):
        self.project = self.get_project()
        return self.model.objects.filter(project=self.project)

    def get_project(self):
        '''Return organization determined by url kwarg'''
        if self.project_url_field not in self.kwargs:
            return None
        return get_object_or_404(
            Project.objects.for_admin_user(user=self.request.user),
            slug=self.kwargs[self.project_url_field]
        )

    def get_context_data(self, **kwargs):
        '''Add organization to context data'''
        context = super(ProjectAdminMixin, self).get_context_data(**kwargs)
        context['project'] = self.get_project()
        return context

    def get_form(self, data=None, files=None, **kwargs):
        '''Pass in organization to form class instance'''
        kwargs['project'] = self.get_project()
        return self.form_class(data, files, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse('projects_domains', args=[self.get_project().slug])
