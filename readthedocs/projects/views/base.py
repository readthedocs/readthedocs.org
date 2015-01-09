from projects.models import Project


class ProjectOnboardMixin(object):
    '''Add project onboard context data to project object views'''

    def get_context_data(self, **kwargs):
        '''Add onboard context data'''
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
