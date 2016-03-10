from django.conf.urls import patterns, url

from readthedocs.core.forms import UserProfileForm

urlpatterns = patterns('',
                       url(r'^create/', 'readthedocs.profiles.views.create_profile',
                           {
                               'form_class': UserProfileForm,
                           },
                           name='profiles_profile_create'),
                       url(r'^edit/', 'readthedocs.profiles.views.edit_profile',
                           {
                               'form_class': UserProfileForm,
                               'template_name': 'profiles/private/edit_profile.html',
                           },
                           name='profiles_profile_edit'),
                       )
