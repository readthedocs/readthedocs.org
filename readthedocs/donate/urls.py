from django.conf.urls import url, patterns, include

from .views import DonateCreateView
from .views import DonateListView
from .views import DonateSuccessView


urlpatterns = patterns(
    '',
    url(r'^$', DonateListView.as_view(), name='donate'),
    url(r'^contribute/$', DonateCreateView.as_view(), name='donate_add'),
    url(r'^contribute/thanks$', DonateSuccessView.as_view(), name='donate_success'),
)
