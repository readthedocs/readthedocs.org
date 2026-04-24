"""Subscriptions views."""

from functools import lru_cache

import structlog
from django.contrib import messages
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus
from vanilla import DetailView
from vanilla import GenericView

from readthedocs.organizations.views.base import OrganizationMixin
from readthedocs.payments.utils import get_stripe_client
from readthedocs.subscriptions.forms import PlanForm
from readthedocs.subscriptions.products import get_product
from readthedocs.subscriptions.utils import get_or_create_stripe_customer
from readthedocs.subscriptions.utils import get_or_create_stripe_subscription


log = structlog.get_logger(__name__)


class DetailSubscription(OrganizationMixin, DetailView):
    """Detail for the subscription of a organization."""

    model = djstripe.Subscription
    form_class = PlanForm
    template_name = "subscriptions/subscription_detail.html"
    context_object_name = "stripe_subscription"

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        # The query argument ``upgraded=true`` is used as a the callback
        # URL for stripe checkout, see `self.redirect_to_checkout`.
        if request.GET.get("upgraded") == "true":
            messages.success(self.request, _("Your plan has been upgraded!"))

        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

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
        stripe_client = get_stripe_client()
        stripe_subscription = self.get_object()
        if not stripe_subscription or stripe_subscription.status != SubscriptionStatus.canceled:
            raise Http404()

        stripe_price = get_object_or_404(djstripe.Price, id=form.cleaned_data["plan"])

        url = self.request.build_absolute_uri(self.get_success_url())
        organization = self.get_organization()
        # pylint: disable=broad-except
        try:
            stripe_customer = get_or_create_stripe_customer(organization)
            checkout_session = stripe_client.checkout.sessions.create(
                params={
                    "customer": stripe_customer.id,
                    "payment_method_types": ["card"],
                    "line_items": [
                        {
                            "price": stripe_price.id,
                            "quantity": 1,
                        }
                    ],
                    "mode": "subscription",
                    "success_url": url + "?upgraded: true",
                    "cancel_url": url,
                }
            )
            return HttpResponseRedirect(checkout_session.url)
        except Exception:
            log.exception(
                "Error while creating a Stripe checkout session.",
                organization_slug=organization.slug,
                price=stripe_price.id,
            )
            messages.error(
                self.request,
                _("There was an error connecting to Stripe, please try again in a few minutes."),
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
        return get_or_create_stripe_subscription(org)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stripe_subscription = self.get_object()
        if stripe_subscription:
            main_product = None
            extra_products = []
            features = {}
            for item in stripe_subscription.items.all().select_related("price__product"):
                rtd_product = get_product(item.price.product.id)
                if not rtd_product:
                    # Skip products that are not defined in RTD_PRODUCTS
                    log.warning(
                        "Product not found in RTD_PRODUCTS",
                        stripe_product_id=item.price.product.id,
                    )
                    continue

                product = {
                    "stripe_price": item.price,
                    "quantity": item.quantity,
                }

                if rtd_product.extra:
                    extra_products.append(product)
                else:
                    main_product = product

                for feature_type, feature in rtd_product.features.items():
                    if feature_type in features:
                        features[feature_type] += feature * item.quantity
                    else:
                        features[feature_type] = feature * item.quantity

            context["main_product"] = main_product
            context["extra_products"] = extra_products
            context["features"] = features.values()
            # When Stripe marks the subscription as ``past_due``,
            # it means the usage of RTD service for the current period/month was not paid at all.
            # Show the end date as the last period the customer paid,
            # or in case the subscription is not paid at all,
            # default to the first unpaid invoice end date.
            context["subscription_end_date"] = stripe_subscription.current_period_end
            if stripe_subscription.status == SubscriptionStatus.past_due:
                latest_paid_invoice = (
                    stripe_subscription.invoices.filter(paid=True).first()
                    or stripe_subscription.invoices.filter(paid=False).last()
                )
                context["subscription_end_date"] = latest_paid_invoice.period_end

        return context

    def get_success_url(self):
        return reverse(
            "subscription_detail",
            args=[self.get_organization().slug],
        )


class StripeCustomerPortal(OrganizationMixin, GenericView):
    """Create a stripe billing portal session for the user to manage their subscription."""

    http_method_names = ["post"]

    def get_success_url(self):
        return reverse(
            "subscription_detail",
            args=[self.get_organization().slug],
        )

    def post(self, request, *args, **kwargs):
        """Redirect the user to the Stripe billing portal."""
        stripe_client = get_stripe_client()
        organization = self.get_organization()
        stripe_customer = organization.stripe_customer
        return_url = request.build_absolute_uri(self.get_success_url())
        try:
            billing_portal = stripe_client.billing_portal.sessions.create(
                params={
                    "customer": stripe_customer.id,
                    "return_url": return_url,
                }
            )
            return HttpResponseRedirect(billing_portal.url)
        except:  # noqa
            log.exception(
                "There was an error connecting to Stripe to create the billing portal session.",
                stripe_customer=stripe_customer.id,
                organization_slug=organization.slug,
            )
            messages.error(
                request,
                _("There was an error connecting to Stripe, please try again in a few minutes"),
            )
            return HttpResponseRedirect(self.get_success_url())
