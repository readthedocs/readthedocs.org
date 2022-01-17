"""Subscriptions views."""

from functools import lru_cache

import stripe
import structlog
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from vanilla import DetailView, GenericView

from readthedocs.organizations.views.base import OrganizationMixin
from readthedocs.subscriptions.forms import PlanForm
from readthedocs.subscriptions.models import Plan, Subscription
from readthedocs.subscriptions.utils import get_or_create_stripe_customer

log = structlog.get_logger(__name__)


class DetailSubscription(OrganizationMixin, DetailView):

    """Detail for the subscription of a organization."""

    model = Subscription
    form_class = PlanForm
    template_name = 'subscriptions/subscription_detail.html'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        # The query argument ``upgraded=true`` is used as a the callback
        # URL for stripe checkout, see `self.redirect_to_checkout`.
        if request.GET.get('upgraded') == 'true':
            messages.success(
                self.request,
                _('Your plan has been upgraded!')
            )

        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST, files=request.FILES)
        if not form.is_valid():
            context = self.get_context_data(form=form)
            return self.render_to_response(context)
        return self.redirect_to_checkout(form)

    def redirect_to_checkout(self, form):
        """
        Redirect to Stripe Checkout for users to buy a subscription.

        Users can buy a new subscription if the current one
        has been deleted after they canceled it.
        """
        subscription = self.get_object()
        if not subscription or subscription.status != 'canceled':
            raise Http404()

        plan = get_object_or_404(Plan, id=form.cleaned_data['plan'])

        url = self.request.build_absolute_uri(self.get_success_url())
        organization = self.get_organization()
        # pylint: disable=broad-except
        try:
            stripe_customer = get_or_create_stripe_customer(organization)
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer.id,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': plan.stripe_id,
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                success_url=url + '?upgraded=true',
                cancel_url=url,
            )
            return HttpResponseRedirect(checkout_session.url)
        except Exception:
            log.exception(
                'Error while creating a Stripe checkout session.',
                organization_slug=organization.slug,
                plan_slug=plan.slug,
            )
            messages.error(
                self.request,
                _('There was an error connecting to Stripe, please try again in a few minutes.'),
            )
            return HttpResponseRedirect(self.get_success_url())

    @lru_cache(maxsize=1)
    def get_object(self):
        """
        Get or create a default subscription for the organization.

        In case an error happened during the organization creation,
        the organization may not have a subscription attached to it.
        We retry the operation when the user visits the subscription page.
        """
        org = self.get_organization()
        return (
            Subscription.objects
            .get_or_create_default_subscription(org)
        )

    def get_success_url(self):
        return reverse(
            'subscription_detail',
            args=[self.get_organization().slug],
        )


class StripeCustomerPortal(OrganizationMixin, GenericView):

    """Create a stripe billing portal session for the user to manage their subscription."""

    http_method_names = ['post']

    def get_success_url(self):
        return reverse(
            'subscription_detail',
            args=[self.get_organization().slug],
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """Redirect the user to the Stripe billing portal."""
        organization = self.get_organization()
        stripe_customer = organization.stripe_id
        return_url = request.build_absolute_uri(self.get_success_url())
        try:
            billing_portal = stripe.billing_portal.Session.create(
                customer=stripe_customer,
                return_url=return_url,
            )
            return HttpResponseRedirect(billing_portal.url)
        except:  # noqa
            log.exception(
                'There was an error connecting to Stripe to create the billing portal session.',
                stripe_customer=stripe_customer,
                organization_slug=organization.slug,
            )
            messages.error(
                request,
                _('There was an error connecting to Stripe, please try again in a few minutes'),
            )
            return HttpResponseRedirect(self.get_success_url())
