from django.conf.urls import url, patterns, include

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.DonateListView.as_view(), name='donate'),
    url(r'^contribute/$', views.DonateCreateView.as_view(), name='donate_add'),
    url(r'^contribute/thanks$', views.DonateSuccessView.as_view(), name='donate_success'),
)
