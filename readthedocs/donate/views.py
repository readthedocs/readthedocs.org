"""Donation views"""

import logging

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.core.cache import cache
from django.http import Http404

from vanilla import CreateView, ListView

from readthedocs.payments.mixins import StripeMixin
from readthedocs.projects.models import Project

from .models import Supporter, SupporterPromo, CLICKS, VIEWS
from .forms import SupporterForm, EthicalAdForm
from .mixins import DonateProgressMixin

log = logging.getLogger(__name__)


class PayAdsView(StripeMixin, CreateView):

    """Create a payment locally and in Stripe"""

    form_class = EthicalAdForm
    success_message = _('Your payment has been received')
    template_name = 'donate/ethicalads.html'

    def get_success_url(self):
        return reverse('pay_success')


class PaySuccess(TemplateView):
    template_name = 'donate/ethicalads-success.html'


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


class PromoDetailView(TemplateView):
    template_name = 'donate/promo_detail.html'

    def get_context_data(self, **kwargs):
        promo_slug = kwargs['promo_slug']
        slugs = promo_slug.split(',')
        days = int(self.request.GET.get('days', 90))

        if promo_slug == 'live' and self.request.user.is_staff:
            promos = SupporterPromo.objects.filter(live=True)
        else:
            promos = SupporterPromo.objects.filter(analytics_id__in=slugs).order_by('analytics_id')

        return {
            'promos': promos,
            'days': days,
            'days_slice': ':%s' % days,
        }


def click_proxy(request, promo_id, hash):
    promo = get_object_or_404(SupporterPromo, pk=promo_id)
    count = cache.get(promo.cache_key(type=CLICKS, hash=hash), None)
    if count is None:
        log.warning('Old or nonexistent hash tried on Click.')
    elif count == 0:
        promo.incr(CLICKS)
        cache.incr(promo.cache_key(type=CLICKS, hash=hash))
        project_slug = cache.get(
            promo.cache_key(type='project', hash=hash),
            None
        )
        if project_slug:
            project = Project.objects.get(slug=project_slug)
            promo.incr(CLICKS, project=project)
    else:
        log.warning('Duplicate click logged. {count} total clicks tried.'.format(count=count))
        cache.incr(promo.cache_key(type=CLICKS, hash=hash))
    return redirect(promo.link)


def view_proxy(request, promo_id, hash):
    promo = get_object_or_404(SupporterPromo, pk=promo_id)
    if not promo.image:
        raise Http404('No image defined for this promo.')
    count = cache.get(promo.cache_key(type=VIEWS, hash=hash), None)
    if count is None:
        log.warning('Old or nonexistent hash tried on View.')
    elif count == 0:
        promo.incr(VIEWS)
        cache.incr(promo.cache_key(type=VIEWS, hash=hash))
        project_slug = cache.get(
            promo.cache_key(type='project', hash=hash),
            None
        )
        if project_slug:
            project = Project.objects.get(slug=project_slug)
            promo.incr(VIEWS, project=project)
    else:
        log.warning('Duplicate view logged. {count} total clicks tried.'.format(count=count))
        cache.incr(promo.cache_key(type=VIEWS, hash=hash))
    return redirect(promo.image)
