'''
Donation views
'''

from django.views.generic import CreateView, ListView
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin

import stripe

from readthedocs.core.mixins import StripeMixin
from .models import OnceUser
from .forms import SupporterForm

import logging

log = logging.getLogger(__name__)


class DonateCreateView(SuccessMessageMixin, StripeMixin, CreateView):
    '''Create a donation locally and in Stripe'''

    form_class = SupporterForm
    success_message = 'Your donation has been added. <3'
    template_name = 'donate/create.html'

    def get_success_url(self):
        return reverse('donate')

    def form_valid(self, form):
        supporter = form.save()
        stripe.api_key = settings.STRIPE_SECRET
        stripe.Charge.create(
            amount=int(form.cleaned_data['dollars']) * 100,
            currency="usd",
            source=form.cleaned_data['stripe_id'],
            description="Read the Docs Sustained Engineering",
        )
        return HttpResponseRedirect(self.get_success_url())


class DonateListView(ListView):
    '''Donation list and detail view'''

    template_name = 'donate/list.html'
    model = OnceUser
    context_object_name = 'supporters'

    def get_queryset(self):
        return OnceUser.objects.filter(public=True)

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self):
        context = super(DonateListView, self).get_context_data()
        sums = (self.model
                .objects.all()
                .aggregate(dollars=Sum('dollars')))
        dollars = sums['dollars'] or 0
        count = OnceUser.objects.count()
        percent = int((float(dollars) / 24000.0) * 100.0)
        context.update({
            'dollars': dollars,
            'percent': percent,
            'count': count,
        })
        return context
