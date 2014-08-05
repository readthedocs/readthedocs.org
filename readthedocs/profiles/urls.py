"""
URLConf for Django user profile management.

Recommended usage is to use a call to ``include()`` in your project's
root URLConf to include this URLConf for any URL beginning with
'/profiles/'.

If the default behavior of the profile views is acceptable to you,
simply use a line like this in your root URLConf to set up the default
URLs for profiles::

    (r'^profiles/', include('profiles.urls')),

But if you'd like to customize the behavior (e.g., by passing extra
arguments to the various views) or split up the URLs, feel free to set
up your own URL patterns for these views instead. If you do, it's a
good idea to keep the name ``profiles_profile_detail`` for the pattern
which points to the ``profile_detail`` view, since several views use
``reverse()`` with that name to generate a default post-submission
redirect. If you don't use that name, remember to explicitly pass
``success_url`` to those views.

"""

from django.conf.urls import *

from profiles import views


urlpatterns = patterns('',
                       url(r'^create/$',
                           views.create_profile,
                           name='profiles_create_profile'),
                       url(r'^edit/$',
                           views.edit_profile,
                           name='profiles_edit_profile'),
                       url(r'^(?P<username>[\w-.]+)/$',
                           views.profile_detail,
                           name='profiles_profile_detail'),
                       url(r'^$',
                           views.ProfileListView.as_view(),
                           name='profiles_profile_list'),
                       )
