'''
Donation views
'''

import logging

from django.views.generic import CreateView, ListView, TemplateView
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import ugettext_lazy as _

from readthedocs.core.mixins import StripeMixin
from .models import Supporter
from .forms import SupporterForm

log = logging.getLogger(__name__)


class DonateCreateView(SuccessMessageMixin, StripeMixin, CreateView):
    '''Create a donation locally and in Stripe'''

    form_class = SupporterForm
    success_message = _('Your contribution has been received')
    template_name = 'donate/create.html'

    def get_success_url(self):
        return reverse('donate_success')


class DonateSuccessView(TemplateView):
    template_name = 'donate/success.html'


class DonateListView(ListView):
    '''Donation list and detail view'''

    template_name = 'donate/list.html'
    model = Supporter
    context_object_name = 'supporters'

    def get_queryset(self):
        return Supporter.objects.filter(public=True)

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self):
        context = super(DonateListView, self).get_context_data()
        sums = (self.model
                .objects.all()
                .aggregate(dollars=Sum('dollars')))
        dollars = sums['dollars'] or 0
        count = Supporter.objects.count()
        percent = int((float(dollars) / 24000.0) * 100.0)
        context.update({
            'dollars': dollars,
            'percent': percent,
            'count': count,
        })
        return context
