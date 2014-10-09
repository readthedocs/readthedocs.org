from django.conf.urls import *

from core.forms import UserProfileForm

urlpatterns = patterns('',
                       url(r'^create/', 'profiles.views.create_profile',
                           {
                               'form_class': UserProfileForm,
                           },
                           name='profiles_profile_create'),
                       url(r'^edit/', 'profiles.views.edit_profile',
                           {
                               'form_class': UserProfileForm,
                               'template_name': 'profiles/private/edit_profile.html',
                           },
                           name='profiles_profile_edit'),
                       )
