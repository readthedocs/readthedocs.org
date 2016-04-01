"""Donation views"""

import logging
import datetime

from django.views.generic import TemplateView
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect

from vanilla import CreateView, ListView
from redis import Redis
import pytz

from readthedocs.payments.mixins import StripeMixin

from .models import Supporter, SupporterPromo
from .forms import SupporterForm
from .mixins import DonateProgressMixin

log = logging.getLogger(__name__)


class DonateCreateView(StripeMixin, CreateView):

    """Create a donation locally and in Stripe"""

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

    """Donation list and detail view"""

    template_name = 'donate/list.html'
    model = Supporter
    context_object_name = 'supporters'

    def get_queryset(self):
        return (Supporter.objects
                .filter(public=True)
                .order_by('-dollars', '-pub_date'))

    def get_template_names(self):
        return [self.template_name]


def click_proxy(request, promo_id, redis=False):
    promo = SupporterPromo.objects.get(pk=promo_id)
    date = pytz.utc.localize(datetime.datetime.utcnow())
    day = datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        tzinfo=pytz.utc,
    )
    if redis:
        redis = Redis.from_url(settings.BROKER_URL)
        redis.incr('{slug}-{year}-{month}-{day}-clicks'.format(
            slug=promo.analytics_id,
            year=day.year,
            month=day.month,
            day=day.day,
        ))
    else:
        impression, _ = promo.impressions.get_or_create(date=day)
        impression.clicks = F('clicks') + 1
        impression.save()
    return redirect(promo.link)


def view_proxy(request, promo_id, hash, redis=False):
    promo = SupporterPromo.objects.get(pk=promo_id)
    date = pytz.utc.localize(datetime.datetime.utcnow())
    day = datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        tzinfo=pytz.utc,
    )
    if redis:
        redis = Redis.from_url(settings.BROKER_URL)
        redis.incr('{slug}-{year}-{month}-{day}-views'.format(
            slug=promo.analytics_id,
            year=day.year,
            month=day.month,
            day=day.day,
        ))
    else:
        impression, _ = promo.impressions.get_or_create(date=day)
        impression.views = F('views') + 1
        impression.save()
    return redirect(promo.image)
