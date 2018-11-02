# -*- coding: utf-8 -*-
"""Gold subscription views."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from vanilla import DeleteView, DetailView, UpdateView

from readthedocs.core.mixins import LoginRequiredMixin
from readthedocs.payments.mixins import StripeMixin
from readthedocs.projects.models import Domain, Project

from .forms import GoldProjectForm, GoldSubscriptionForm
from .models import GoldUser


class GoldSubscriptionMixin(SuccessMessageMixin, StripeMixin,
                            LoginRequiredMixin):

    """Gold subscription mixin for view classes."""

    model = GoldUser
    form_class = GoldSubscriptionForm

    def get_object(self):
        try:
            return self.get_queryset().get(user=self.request.user)
        except self.model.DoesNotExist:
            return None

    def get_form(self, data=None, files=None, **kwargs):
        """Pass in copy of POST data to avoid read only QueryDicts."""
        kwargs['customer'] = self.request.user
        return super(GoldSubscriptionMixin, self).get_form(data, files, **kwargs)

    def get_success_url(self, **__):
        return reverse_lazy('gold_detail')

    def get_template_names(self):
        return ('gold/subscription{0}.html'.format(self.template_name_suffix))

    def get_context_data(self, **kwargs):
        context = super(GoldSubscriptionMixin, self).get_context_data(**kwargs)
        domains = Domain.objects.filter(project__users=self.request.user)
        context['domains'] = domains
        return context


# Subscription Views


class DetailGoldSubscription(GoldSubscriptionMixin, DetailView):

    def get(self, request, *args, **kwargs):
        """
        GET handling for this view.

        If there is a gold subscription instance, then we show the normal detail
        page, otherwise show the registration form
        """
        resp = super(DetailGoldSubscription, self).get(request, *args, **kwargs)
        if self.object is None:
            return HttpResponseRedirect(reverse('gold_subscription'))
        return resp


class UpdateGoldSubscription(GoldSubscriptionMixin, UpdateView):
    success_message = _('Your subscription has been updated')


class DeleteGoldSubscription(GoldSubscriptionMixin, DeleteView):

    """
    Delete Gold subscription view.

    On object deletion, the corresponding Stripe customer is deleted as well.
    Deletion is triggered on subscription deletion using a signal, ensuring the
    subscription is synced with Stripe.
    """

    success_message = _('Your subscription has been cancelled')

    def post(self, request, *args, **kwargs):
        """Add success message to delete post."""
        resp = super(DeleteGoldSubscription, self).post(request, *args, **kwargs)
        success_message = self.get_success_message({})
        if success_message:
            messages.success(self.request, success_message)
        return resp


@login_required
def projects(request):
    gold_user = get_object_or_404(GoldUser, user=request.user)
    gold_projects = gold_user.projects.all()

    if request.method == 'POST':
        form = GoldProjectForm(
            active_user=request.user, data=request.POST, user=gold_user, projects=gold_projects)
        if form.is_valid():
            to_add = Project.objects.get(slug=form.cleaned_data['project'])
            gold_user.projects.add(to_add)
            return HttpResponseRedirect(reverse('gold_projects'))
    else:
        # HACK: active_user=request.user is passed
        # as argument to get the currently active
        # user in the GoldProjectForm which is used
        # to filter the choices based on the user.
        form = GoldProjectForm(active_user=request.user)

    return render(
        request, 'gold/projects.html', {
            'form': form,
            'gold_user': gold_user,
            'publishable': settings.STRIPE_PUBLISHABLE,
            'user': request.user,
            'projects': gold_projects,
        })


@login_required
def projects_remove(request, project_slug):
    gold_user = get_object_or_404(GoldUser, user=request.user)
    project = get_object_or_404(Project.objects.all(), slug=project_slug)
    gold_user.projects.remove(project)
    return HttpResponseRedirect(reverse('gold_projects'))
