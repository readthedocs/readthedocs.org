"""Gold subscription views."""

import json

import structlog
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from djstripe.enums import APIKeyType
from djstripe.models import APIKey
from vanilla import DetailView
from vanilla import FormView
from vanilla import GenericView

from readthedocs.core.mixins import PrivateViewMixin
from readthedocs.payments.utils import get_stripe_client
from readthedocs.projects.models import Project

from .forms import GoldProjectForm
from .forms import GoldSubscriptionForm
from .models import GoldUser


log = structlog.get_logger(__name__)


class GoldSubscription(
    PrivateViewMixin,
    DetailView,
    FormView,
):
    """Gold subscription view."""

    model = GoldUser
    form_class = GoldSubscriptionForm
    template_name = "gold/subscription_detail.html"

    def get(self, *args, **kwargs):
        subscribed = self.request.GET.get("subscribed", None)
        if subscribed == "true":
            messages.success(
                self.request,
                "Thanks for supporting Read the Docs! It really means a lot to us.",
            )

        return super().get(*args, **kwargs)

    def get_object(self):
        try:
            return self.get_queryset().get(user=self.request.user)
        except self.model.DoesNotExist:
            return None

    def get_success_url(self, **__):
        return reverse_lazy("gold_detail")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["golduser"] = self.get_object()
        context["stripe_publishable"] = (
            APIKey.objects.filter(type=APIKeyType.publishable).first().secret
        )
        return context


class GoldProjectsMixin(PrivateViewMixin):
    def get_gold_user(self):
        return get_object_or_404(GoldUser, user=self.request.user)

    def get_gold_projects(self):
        return self.get_gold_user().projects.all()

    def get_success_url(self):
        return reverse_lazy("gold_projects")


class GoldProjectsListCreate(GoldProjectsMixin, FormView):
    """Gold Project list view and form view."""

    form_class = GoldProjectForm
    template_name = "gold/projects.html"

    def form_valid(self, form):
        to_add = Project.objects.get(slug=form.cleaned_data["project"])
        gold_user = self.get_gold_user()
        gold_user.projects.add(to_add)
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["user"] = self.get_gold_user()
        kwargs["projects"] = self.get_gold_projects()
        return self.form_class(self.request.user, data, files, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gold_user"] = self.get_gold_user()
        context["user"] = self.request.user
        context["projects"] = self.get_gold_projects()
        return context


class GoldProjectRemove(GoldProjectsMixin, GenericView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        gold_user = self.get_gold_user()

        project = get_object_or_404(Project.objects.all(), slug=self.kwargs.get("project_slug"))
        gold_user.projects.remove(project)

        return HttpResponseRedirect(self.get_success_url())


class GoldCreateCheckoutSession(GenericView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            schema = "https" if settings.PUBLIC_DOMAIN_USES_HTTPS else "http"
            url = reverse_lazy("gold_detail")
            url = f"{schema}://{settings.PRODUCTION_DOMAIN}{url}"
            price = json.loads(request.body).get("priceId")
            log.info(
                "Creating Stripe Checkout Session.",
                user_username=user.username,
                price=price,
            )
            stripe_client = get_stripe_client()
            checkout_session = stripe_client.checkout.sessions.create(
                params={
                    "client_reference_id": user.username,
                    "customer_email": user.emailaddress_set.filter(verified=True).first()
                    or user.email,
                    "payment_method_types": ["card"],
                    "line_items": [
                        {
                            "price": price,
                            "quantity": 1,
                        }
                    ],
                    "mode": "subscription",
                    # We use the same URL to redirect the user. We only show a different notification.
                    "success_url": f"{url}?subscribed=true",
                    "cancel_url": f"{url}?subscribed=false",
                }
            )
            return JsonResponse({"session_id": checkout_session.id})
        except:  # noqa
            log.exception("There was an error connecting to Stripe.")
            return JsonResponse(
                {"error": "There was an error connecting to Stripe."},
                status=500,
            )


class GoldSubscriptionPortal(GenericView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        user = request.user

        # TODO: review if User <-> GoldUser being ``ForeignKey`` makes
        # sense no that we are removing the one time donation
        stripe_customer = user.gold.first().stripe_id

        scheme = "https" if settings.PUBLIC_DOMAIN_USES_HTTPS else "http"
        return_url = f"{scheme}://{settings.PRODUCTION_DOMAIN}" + str(self.get_success_url())
        try:
            stripe_client = get_stripe_client()
            billing_portal = stripe_client.billing_portal.sessions.create(
                params={
                    "customer": stripe_customer,
                    "return_url": return_url,
                }
            )
            return HttpResponseRedirect(billing_portal.url)
        except:  # noqa
            log.exception(
                "There was an error connecting to Stripe.",
                user_userame=user.username,
                stripe_customer=stripe_customer,
            )
            messages.error(
                request,
                _("There was an error connecting to Stripe, please try again in a few minutes"),
            )
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("gold_detail")
