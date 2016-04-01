from django.conf.urls import url, patterns, include

from .views import DonateCreateView
from .views import DonateListView
from .views import DonateSuccessView
from .views import click_proxy, view_proxy


urlpatterns = patterns(
    '',
    url(r'^$', DonateListView.as_view(), name='donate'),
    url(r'^contribute/$', DonateCreateView.as_view(), name='donate_add'),
    url(r'^contribute/thanks$', DonateSuccessView.as_view(), name='donate_success'),
    url(r'^view/(?P<promo_id>\d+)/(?P<hash>.+)/$', view_proxy, name='donate_view_proxy'),
    url(r'^click/(?P<promo_id>\d+)/(?P<hash>.+)/$', click_proxy, name='donate_click_proxy'),
)
