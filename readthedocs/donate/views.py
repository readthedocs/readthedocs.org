"""Donation views"""
# We use 'hash' heavily in the API here.
# pylint: disable=redefined-builtin

from __future__ import absolute_import
import logging

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.http import Http404

from vanilla import CreateView, ListView

from readthedocs.donate.utils import offer_promo
from readthedocs.payments.mixins import StripeMixin
from readthedocs.projects.models import Project
from readthedocs.redirects.utils import get_redirect_response

from .models import Supporter, SupporterPromo
from .constants import CLICKS, VIEWS
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
        days = int(self.request.GET.get('days', 90))

        if promo_slug == 'live' and self.request.user.is_staff:
            promos = SupporterPromo.objects.filter(live=True)
        elif promo_slug[-1] == '*' and '-' in promo_slug:
            promos = SupporterPromo.objects.filter(
                analytics_id__contains=promo_slug.replace('*', '')
            )
        else:
            slugs = promo_slug.split(',')
            promos = SupporterPromo.objects.filter(analytics_id__in=slugs)

        total_clicks = sum(promo.total_clicks() for promo in promos)

        return {
            'promos': promos,
            'total_clicks': total_clicks,
            'days': days,
            'days_slice': ':%s' % days,
        }


def click_proxy(request, promo_id, hash):
    """Track a click on a promotion and redirect to the link."""
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
        agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        log.warning(
            'Duplicate click logged. {count} total clicks tried. User Agent: [{agent}]'.format(
                count=count, agent=agent
            )
        )
        cache.incr(promo.cache_key(type=CLICKS, hash=hash))
        raise Http404('Invalid click. This has been logged.')
    return redirect(promo.link)


def view_proxy(request, promo_id, hash):
    """Track a view of a promotion and redirect to the image."""
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
        agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        log.warning(
            'Duplicate view logged. {count} total views tried. User Agent: [{agent}]'.format(
                count=count, agent=agent
            )
        )
        cache.incr(promo.cache_key(type=VIEWS, hash=hash))
        raise Http404('Invalid click. This has been logged.')
    return redirect(promo.image)


def _add_promo_data(display_type):
    promo_queryset = SupporterPromo.objects.filter(live=True, display_type=display_type)
    promo_obj = promo_queryset.order_by('?').first()
    if promo_obj:
        promo_dict = offer_promo(promo_obj=promo_obj, project=None)
    else:
        promo_dict = None
    return promo_dict


def promo_500(request, template_name='donate/promo_500.html', **__):
    """A simple 500 handler so we get media"""
    promo_dict = _add_promo_data(display_type='error')
    r = render_to_response(template_name,
                           context_instance=RequestContext(request),
                           context={
                               'promo_data': promo_dict,
                           })
    r.status_code = 500
    return r


def promo_404(request, template_name='donate/promo_404.html', **__):
    """A simple 404 handler so we get media"""
    promo_dict = _add_promo_data(display_type='error')
    response = get_redirect_response(request, path=request.get_full_path())
    if response:
        return response
    r = render_to_response(template_name,
                           context_instance=RequestContext(request),
                           context={
                               'promo_data': promo_dict,
                           })
    r.status_code = 404
    return r
