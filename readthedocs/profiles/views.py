"""Views for creating, editing and viewing site-specific user profiles."""

from datetime import timedelta

from allauth.account.views import LoginView as AllAuthLoginView
from allauth.account.views import LogoutView as AllAuthLogoutView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
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

from readthedocs.audit.filters import UserSecurityLogFilter
from readthedocs.audit.models import AuditLog
from readthedocs.core.forms import (
    UserAdvertisingForm,
    UserDeleteForm,
    UserProfileForm,
)
from readthedocs.core.history import safe_update_change_reason
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.models import UserProfile
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.utils import get_csv_file


class LoginViewBase(AllAuthLoginView):

    pass


class LoginView(SettingsOverrideObject):

    _default_class = LoginViewBase


class LogoutViewBase(AllAuthLogoutView):

    pass


class LogoutView(SettingsOverrideObject):

    _default_class = LogoutViewBase


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


class AccountDelete(PrivateViewMixin, SuccessMessageMixin, FormView):

    form_class = UserDeleteForm
    template_name = 'profiles/private/delete_account.html'
    success_message = _('You have successfully deleted your account')

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)

    def form_valid(self, form):
        user = self.get_object()
        logout(self.request)
        user.delete()
        safe_update_change_reason(user, 'Changed from: form')
        return super().form_valid(form)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['instance'] = self.get_object()
        kwargs['initial'] = {'username': ''}
        return super().get_form(data, files, **kwargs)

    def get_success_url(self):
        return reverse('homepage')


class ProfileDetailBase(DetailView):

    model = User
    template_name = 'profiles/public/profile_detail.html'
    lookup_field = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object().profile
        return context


class ProfileDetail(SettingsOverrideObject):

    _default_class = ProfileDetailBase


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


class UserSecurityLogView(PrivateViewMixin, ListView):
    model = AuditLog
    template_name = 'profiles/private/security_log.html'
    days_limit = settings.RTD_DEFAULT_LOGS_RETENTION_DAYS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def _get_csv_data(self):
        headers = [
            'Date',
            'User',
            'Project',
            'Organization',
            'Action',
            'IP',
            'Browser',
        ]
        data = (
            self._get_queryset()
            .values_list(
                'created',
                'log_user_username',
                'log_project_slug',
                'log_organization_slug',
                'action',
                'ip',
                'browser',
            )
        )
        now = timezone.now()
        days_ago = now - timedelta(days=self.days_limit)
        filename = 'readthedocs_user_security_logs_{username}_{start}_{end}.csv'.format(
            username=self.request.user.username,
            start=timezone.datetime.strftime(days_ago, '%Y-%m-%d'),
            end=timezone.datetime.strftime(now, '%Y-%m-%d'),
        )
        csv_data = [
            [
                timezone.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'),
                *rest
            ]
            for date, *rest in data
        ]
        csv_data.insert(0, headers)
        return get_csv_file(filename=filename, csv_data=csv_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['days_limit'] = self.days_limit
        context['filter'] = self.filter
        return context

    def _get_queryset(self):
        user = self.request.user
        days_ago = timezone.now() - timedelta(days=self.days_limit)
        queryset = AuditLog.objects.filter(
            user=user,
            action__in=[AuditLog.AUTHN, AuditLog.AUTHN_FAILURE],
            created__gte=days_ago,
        )
        return queryset

    def get_queryset(self):
        queryset = self._get_queryset()
        # Set filter on self, so we can use it in the context.
        # Without executing it twice.
        self.filter = UserSecurityLogFilter(
            self.request.GET,
            queryset=queryset,
        )
        # If an invalid ip was passed, dont filter it.
        # Otherwise django will raise an error when executing the queryset.
        if self.filter.is_valid():
            return self.filter.qs
        return queryset.none()
