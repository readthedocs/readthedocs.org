"""Django URL patterns for the donate app."""

from __future__ import absolute_import
from django.conf.urls import url

from .views import DonateCreateView, DonateListView, DonateSuccessView
from .views import PayAdsView, PaySuccess, PromoDetailView
from .views import click_proxy, view_proxy


urlpatterns = [
    url(r'^$', DonateListView.as_view(), name='donate'),
    url(r'^pay/$', PayAdsView.as_view(), name='pay_ads'),
    url(r'^pay/success/$', PaySuccess.as_view(), name='pay_success'),
    url(r'^report/(?P<promo_slug>.+)/$', PromoDetailView.as_view(), name='donate_promo_detail'),
    url(r'^contribute/$', DonateCreateView.as_view(), name='donate_add'),
    url(r'^contribute/thanks$', DonateSuccessView.as_view(), name='donate_success'),
    url(r'^view/(?P<promo_id>\d+)/(?P<hash>.+)/$', view_proxy, name='donate_view_proxy'),
    url(r'^click/(?P<promo_id>\d+)/(?P<hash>.+)/$', click_proxy, name='donate_click_proxy'),
]
