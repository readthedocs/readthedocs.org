"""Views for creating, editing and viewing site-specific user profiles."""

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token
from vanilla import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from readthedocs.core.forms import (
    UserAdvertisingForm,
    UserDeleteForm,
    UserProfileForm,
)
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.models import UserProfile
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.utils import get_projects_only_owner


class ProfileEdit(PrivateViewMixin, UpdateView):

    """Edit the current user's profile."""

    model = UserProfile
    form_class = UserProfileForm
    template_name = 'profiles/private/edit_profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse(
            'profiles_profile_detail',
            kwargs={'username': self.request.user.username},
        )


class BaseAccountDelete(PrivateViewMixin, SuccessMessageMixin, FormView):

    form_class = UserDeleteForm
    template_name = 'profiles/private/delete_account.html'
    success_message = _('You have successfully deleted your account')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        self.request.user.delete()
        logout(self.request)
        return super().form_valid(form)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['instance'] = self.get_object()
        return super().get_form(data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_objects_to_be_deleted())
        return context

    def get_objects_to_be_deleted(self):
        """Return an additional context with objects to be deleted to show in the template."""
        return {
            'projects_to_be_deleted': get_projects_only_owner(self.request.user),
        }

    def get_success_url(self):
        return reverse('homepage')


class AccountDelete(SettingsOverrideObject):

    _default_class = BaseAccountDelete


class ProfileDetail(DetailView):

    model = User
    template_name = 'profiles/public/profile_detail.html'
    lookup_field = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object().profile
        return context


class AccountAdvertisingEdit(PrivateViewMixin, SuccessMessageMixin, UpdateView):

    model = UserProfile
    form_class = UserAdvertisingForm
    context_object_name = 'profile'
    template_name = 'profiles/private/advertising_profile.html'
    success_message = _('Updated your advertising preferences')

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse('account_advertising')


class TokenMixin(PrivateViewMixin):

    """User token to access APIv3."""

    model = Token
    lookup_url_kwarg = 'token_pk'
    template_name = 'profiles/private/token_list.html'

    def get_queryset(self):
        # NOTE: we are currently showing just one token since the DRF model has
        # a OneToOneField relation with User. Although, we plan to have multiple
        # scope-based tokens.
        return Token.objects.filter(user__in=[self.request.user])

    def get_success_url(self):
        return reverse('profiles_tokens')


class TokenListView(TokenMixin, ListView):
    pass


class TokenCreateView(TokenMixin, CreateView):

    """Simple view to generate a Token object for the logged in User."""

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        _, created = Token.objects.get_or_create(user=self.request.user)
        if created:
            messages.info(request, 'API Token created successfully')
        return HttpResponseRedirect(self.get_success_url())


class TokenDeleteView(TokenMixin, DeleteView):

    """View to delete/revoke the current Token of the logged in User."""

    http_method_names = ['post']

    def get_object(self, queryset=None):  # noqa
        return self.request.user.auth_token
