'''
Donation views
'''

import logging

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import ugettext_lazy as _
from vanilla import CreateView, ListView

from readthedocs.payments.mixins import StripeMixin

from .models import Supporter
from .forms import SupporterForm
from .mixins import DonateProgressMixin

log = logging.getLogger(__name__)


class DonateCreateView(StripeMixin, CreateView):
    '''Create a donation locally and in Stripe'''

    form_class = SupporterForm
    success_message = _('Your contribution has been received')
    template_name = 'donate/create.html'

    def get_success_url(self):
        return reverse('donate_success')

    def get_initial(self):
        return {'dollars': self.request.GET.get('dollars', 50)}

    def get_form(self, data=None, files=None, **kwargs):
        kwargs['user'] = self.request.user
        return super(DonateCreateView, self).get_form(data, files, **kwargs)


class DonateSuccessView(TemplateView):
    template_name = 'donate/success.html'


class DonateListView(DonateProgressMixin, ListView):
    '''Donation list and detail view'''

    template_name = 'donate/list.html'
    model = Supporter
    context_object_name = 'supporters'

    def get_queryset(self):
        return (Supporter.objects
                .filter(public=True)
                .order_by('-dollars', '-pub_date'))

    def get_template_names(self):
        return [self.template_name]
