"""Views for creating, editing and viewing site-specific user profiles."""

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
from django.utils.translation import gettext_lazy as _
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
from readthedocs.core.history import set_change_reason
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
        set_change_reason(user, self.get_change_reason())
        user.delete()
        return super().form_valid(form)

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['instance'] = self.get_object()
        kwargs['initial'] = {'username': ''}
        return super().get_form(data, files, **kwargs)

    def get_success_url(self):
        return reverse('homepage')

    def get_change_reason(self):
        klass = self.__class__.__name__
        return f'origin=form class={klass}'


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
    days_limit = settings.RTD_AUDITLOGS_DEFAULT_RETENTION_DAYS

    def get(self, request, *args, **kwargs):
        download_data = request.GET.get('download', False)
        if download_data:
            return self._get_csv_data()
        return super().get(request, *args, **kwargs)

    def _get_start_date(self):
        """Get the date to show logs from."""
        creation_date = self.request.user.date_joined.date()
        start_date = timezone.now().date() - timezone.timedelta(days=self.days_limit)
        # The max we can go back is to the creation of the user.
        return max(start_date, creation_date)

    def _get_csv_data(self):
        current_timezone = settings.TIME_ZONE
        values = [
            (f'Date ({current_timezone})', 'created'),
            ('User', 'log_user_username'),
            ('Project', 'log_project_slug'),
            ('Organization', 'log_organization_slug'),
            ('Action', 'action'),
            ('IP', 'ip'),
            ('Browser', 'browser'),
        ]
        data = self.get_queryset().values_list(*[value for _, value in values])

        start_date = self._get_start_date()
        end_date = timezone.now().date()
        date_filter = self.filter.form.cleaned_data.get('date')
        if date_filter:
            start_date = date_filter.start or start_date
            end_date = date_filter.stop or end_date

        filename = 'readthedocs_user_security_logs_{username}_{start}_{end}.csv'.format(
            username=self.request.user.username,
            start=timezone.datetime.strftime(start_date, '%Y-%m-%d'),
            end=timezone.datetime.strftime(end_date, '%Y-%m-%d'),
        )
        csv_data = [
            [timezone.datetime.strftime(date, '%Y-%m-%d %H:%M:%S'), *rest]
            for date, *rest in data
        ]
        csv_data.insert(0, [header for header, _ in values])
        return get_csv_file(filename=filename, csv_data=csv_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['days_limit'] = self.days_limit
        context['filter'] = self.filter
        context['AuditLog'] = AuditLog
        return context

    def _get_queryset(self):
        """Return the queryset without filters."""
        user = self.request.user
        start_date = self._get_start_date()
        queryset = AuditLog.objects.filter(
            user=user,
            action__in=[AuditLog.AUTHN, AuditLog.AUTHN_FAILURE],
            created__gte=start_date,
        )
        return queryset

    def get_queryset(self):
        """
        Return the queryset with filters.

        If you want the original queryset without filters,
        use `_get_queryset`.
        """
        queryset = self._get_queryset()
        # Set filter on self, so we can use it in the context.
        # Without executing it twice.
        self.filter = UserSecurityLogFilter(
            self.request.GET,
            queryset=queryset,
        )
        return self.filter.qs
