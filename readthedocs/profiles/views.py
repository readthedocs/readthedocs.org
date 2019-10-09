"""Views for creating, editing and viewing site-specific user profiles."""

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, UpdateView
from rest_framework.authtoken.models import Token

from readthedocs.core.forms import (
    UserAdvertisingForm,
    UserDeleteForm,
    UserProfileForm,
)
from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.core.models import UserProfile


class EditProfile(PrivateViewMixin, UpdateView):

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


@login_required()
def delete_account(request):
    form = UserDeleteForm()
    template_name = 'profiles/private/delete_account.html'

    if request.method == 'POST':
        form = UserDeleteForm(instance=request.user, data=request.POST)
        if form.is_valid():
            # Delete the user permanently
            # It will also delete some projects where the user is the only owner
            request.user.delete()
            logout(request)
            messages.info(request, 'You have successfully deleted your account')

            return redirect('homepage')

    return render(request, template_name, {'form': form})


def profile_detail(
        request,
        username,
        public_profile_field=None,
        template_name='profiles/public/profile_detail.html',
        extra_context=None,
):
    """
    Detail view of a user's profile.

    If the user does not exists, ``Http404`` will be raised.

    **Required arguments:**

    ``username``
        The username of the user whose profile is being displayed.

    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``public_profile_field``
        The name of a ``BooleanField`` on the profile model; if the
        value of that field on the user's profile is ``False``, the
        ``profile`` variable in the template will be ``None``. Use
        this feature to allow users to mark their profiles as not
        being publicly viewable.

        If this argument is not specified, it will be assumed that all
        users' profiles are publicly viewable.

    ``template_name``
        The name of the template to use for displaying the profile. If
        not specified, this will default to
        :template:`profiles/profile_detail.html`.

    **Context:**

    ``profile``
        The user's profile, or ``None`` if the user's profile is not
        publicly viewable (see the description of
        ``public_profile_field`` above).

    **Template:**

    ``template_name`` keyword argument or
    :template:`profiles/profile_detail.html`.
    """
    user = get_object_or_404(User, username=username)
    profile_obj = user.profile
    if (public_profile_field is not None and
            not getattr(profile_obj, public_profile_field)):
        profile_obj = None

    if extra_context is None:
        extra_context = {}
    context = {
        key: value() if callable(value) else value
        for key, value in extra_context.items()
    }
    context.update({'profile': profile_obj})
    return render(request, template_name, context=context)


@login_required
def account_advertising(request):
    success_url = reverse(account_advertising)
    profile_obj = request.user.profile
    if request.method == 'POST':
        form = UserAdvertisingForm(
            data=request.POST,
            instance=profile_obj,
        )
        if form.is_valid():
            form.save()
            messages.info(request, _('Updated your advertising preferences'))
            return HttpResponseRedirect(success_url)
    else:
        form = UserAdvertisingForm(instance=profile_obj)

    return render(
        request,
        'profiles/private/advertising_profile.html',
        context={
            'form': form,
            'profile': profile_obj,
            'user': profile_obj.user,
        },
    )


class TokenMixin(PrivateViewMixin):

    """User token to access APIv3."""

    model = Token
    lookup_url_kwarg = 'token_pk'
    template_name = 'profiles/private/token_list.html'

    def get_queryset(self):
        # Token has a OneToOneField relation with User
        return Token.objects.filter(user__in=[self.request.user])

    def get_success_url(self):
        return reverse(
            'projects_token',
            args=[self.get_project().slug],
        )


class TokenList(TokenMixin, ListView):
    pass
