from django.conf.urls import url, patterns, include


from gold import views

urlpatterns = patterns('',
                       url(r'^register/$', views.register, name='gold_register'),
                       url(r'^edit/$', views.edit, name='gold_edit'),
                       url(r'^cancel/$', views.cancel, name='gold_cancel'),
                       url(r'^once/$', views.once, name='gold_once'),
                       url(r'^thanks/$', views.thanks, name='gold_thanks'),
                       )
