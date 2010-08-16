from django.conf.urls.defaults import *

urlpatterns = patterns('watching.views',
    url(r'^$',
        'pageview_list',
        name='pageviews_list'
    ),
)
