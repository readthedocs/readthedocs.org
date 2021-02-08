# -*- coding: utf-8 -*-

"""Gold subscription views."""

import json
import logging
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from vanilla import DeleteView, DetailView, FormView, GenericView, UpdateView
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.core.mixins import PrivateViewMixin
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
            user = request.user
            schema = 'https' if settings.PUBLIC_DOMAIN_USES_HTTPS else 'http'
            url = reverse('gold_subscription')
            url = f'{schema}://{settings.PRODUCTION_DOMAIN}{url}'
            price = json.loads(request.body).get('priceId')
            log.info('Creating Stripe Checkout Session. user=%s price=%s', user, price)
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=user.username,
                customer_email=user.emailaddress_set.filter(verified=True).first() or user.email,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price,
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                # We use the same URL to redirect the user. We only show a different notification.
                success_url=url,
                cancel_url=url,
            )
            return JsonResponse({'session_id': checkout_session.id})
        except:  # noqa
            log.exception('There was an error connecting to Stripe.')
            return JsonResponse(
                {
                    'error': 'There was an error connecting to Stripe.'
                },
                status=500,
            )


class GoldSubscriptionPortal(GenericView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        user = request.user

        # TODO: review if User <-> GoldUser being ``ManyToManyField`` makes
        # sense no that we are removing the one time donation
        stripe_customer = user.gold.first().stripe_id

        scheme = 'https' if settings.PUBLIC_DOMAIN_USES_HTTPS else 'http'
        return_url = f'{scheme}://{settings.PRODUCTION_DOMAIN}' + str(self.get_success_url())
        try:
            billing_portal = stripe.billing_portal.Session.create(
                customer=stripe_customer,
                return_url=return_url,
            )
            return HttpResponseRedirect(billing_portal.url)
        except:  # noqa
            messages.error(
                request,
                _('There was an error connecting to Stripe, please try again in a few minutes'),
            )
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gold_detail')


# TODO: where this code should live? (readthedocs-ext?)
# Should we move all GoldUser code to readthedocs-ext?
class StripeEventView(APIView):

    """Endpoint for Stripe events."""

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)

    EVENT_CHECKOUT_PAYMENT_FAILED = 'checkout.session.async_payment_failed'
    EVENT_CHECKOUT_PAYMENT_SUCCEEDED = 'checkout.session.async_payment_succeeded'
    EVENT_CHECKOUT_COMPLETED = 'checkout.session.completed'
    EVENT_CUSTOMER_SUBSCRIPTION_UPDATED = 'customer.subscription.updated'

    EVENTS = [
        EVENT_CHECKOUT_PAYMENT_SUCCEEDED,
        EVENT_CHECKOUT_COMPLETED,
        EVENT_CUSTOMER_SUBSCRIPTION_UPDATED,
    ]

    def post(self, request, format=None):
        try:
            event = stripe.Event.construct_from(request.data, settings.STRIPE_SECRET)
            if event.type in self.EVENTS:
                stripe_customer = event.data.object.customer

                if event.type == self.EVENT_CHECKOUT_COMPLETED:
                    username = event.data.object.client_reference_id
                    subscription = stripe.Subscription.retrieve(event.data.object.subscription)

                    user = User.objects.get(username=username)
                    GoldUser.objects.create(
                        user=user,
                        level=subscription.plan.id,
                        stripe_id=stripe_customer,
                        subscribed=True,
                    )
                    # TODO: add user notification saying it was successful

                elif event.type == self.EVENT_CHECKOUT_PAYMENT_FAILED:
                    username = event.data.object.client_reference_id
                    # TODO: add user notification saying it failed
                    log.exception(
                        'Gold User payment failed. username=%s customer=%s',
                        username,
                        stripe_customer,
                    )

                elif event.type == self.EVENT_CUSTOMER_SUBSCRIPTION_UPDATED:
                    # TODO: check if the subscription was canceled, past due,
                    # etc and take the according action
                    level = event.data.object.plan.id
                    log.info(
                        'Gold User subscription updated. customer=%s level=%s',
                        stripe_customer,
                        level,
                    )
                    (
                        GoldUser.objects
                        .filter(stripe_id=stripe_customer)
                        .update(
                            level=level,
                            modified_date=timezone.now(),
                        )
                    )

                return Response({
                    'OK': True,
                })
        except Exception:
            log.exception('Unexpected data in Stripe Event object')
            return Response(
                {
                    'OK': False,
                },
                status=500,
            )
