# -*- coding: utf-8 -*-

"""Gold subscription views."""

import json
import logging
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from vanilla import DeleteView, DetailView, FormView, GenericView, UpdateView

from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.payments.mixins import StripeMixin
from readthedocs.projects.models import Domain, Project

from .forms import GoldProjectForm, GoldSubscriptionForm
from .models import GoldUser, LEVEL_CHOICES


log = logging.getLogger(__name__)


class GoldSubscriptionMixin(
        SuccessMessageMixin,
        PrivateViewMixin,
):

    """Gold subscription mixin for view classes."""

    model = GoldUser
    form_class = GoldSubscriptionForm

    def get_object(self):
        try:
            return self.get_queryset().get(user=self.request.user)
        except self.model.DoesNotExist:
            return None

    def get_success_url(self, **__):
        return reverse_lazy('gold_detail')

    def get_template_names(self):
        return ('gold/subscription{}.html'.format(self.template_name_suffix))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        domains = Domain.objects.filter(project__users=self.request.user)
        context['domains'] = domains
        context['stripe_publishable'] = settings.STRIPE_PUBLISHABLE
        return context


# Subscription Views


class DetailGoldSubscription(GoldSubscriptionMixin, DetailView):

    def get(self, request, *args, **kwargs):
        """
        GET handling for this view.

        If there is a gold subscription instance, then we show the normal detail
        page, otherwise show the registration form
        """
        resp = super().get(request, *args, **kwargs)
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
        resp = super().post(request, *args, **kwargs)
        success_message = self.get_success_message({})
        if success_message:
            messages.success(self.request, success_message)
        return resp


class GoldProjectsMixin(PrivateViewMixin):

    def get_gold_user(self):
        return get_object_or_404(GoldUser, user=self.request.user)

    def get_gold_projects(self):
        return self.get_gold_user().projects.all()

    def get_success_url(self):
        return reverse('gold_projects')


class GoldProjectsListCreate(GoldProjectsMixin, FormView):

    """Gold Project list view and form view."""

    form_class = GoldProjectForm
    template_name = 'gold/projects.html'

    def form_valid(self, form):
        to_add = Project.objects.get(slug=form.cleaned_data['project'])
        gold_user = self.get_gold_user()
        gold_user.projects.add(to_add)
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['user'] = self.get_gold_user()
        kwargs['projects'] = self.get_gold_projects()
        return self.form_class(self.request.user, data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gold_user'] = self.get_gold_user()
        context['publishable'] = settings.STRIPE_PUBLISHABLE
        context['user'] = self.request.user
        context['projects'] = self.get_gold_projects()
        return context


class GoldProjectRemove(GoldProjectsMixin, GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # pylint: disable=unused-argument
        gold_user = self.get_gold_user()

        project = get_object_or_404(
            Project.objects.all(),
            slug=self.kwargs.get('project_slug')
        )
        gold_user.projects.remove(project)

        return HttpResponseRedirect(self.get_success_url())


class GoldCreateCheckoutSession(GenericView):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            schema = 'https' if settings.PUBLIC_DOMAIN_USES_HTTPS else 'http'
            success_url = reverse('gold_checkout_success')
            success_url = f'{schema}://{settings.PRODUCTION_DOMAIN}{success_url}'
            cancel_url = reverse('gold_checkout_cancel')
            cancel_url = f'{schema}://{settings.PRODUCTION_DOMAIN}{cancel_url}'
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': json.loads(request.body).get('priceId'),
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return JsonResponse({'session_id': checkout_session.id})
        except:  # noqa
            log.exception('There was an error connecting to Stripe.')
            return JsonResponse({'error': 'There was an error connecting to Stripe.'}, status=500)


class GoldSubscriptionPortal(GenericView):
    pass
