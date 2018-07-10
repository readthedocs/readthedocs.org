# -*- coding: utf-8 -*-
"""
Views to handle SSH key management under Project Admin's Dashboard.

.. note::

    This functionality is not enabled by default. Views and models from this
    application are not exposed to the user.
"""
from __future__ import division, print_function, unicode_literals

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from vanilla import (
    CreateView, DeleteView, DetailView, FormView, ListView, TemplateView)

from readthedocs.projects.views.mixins import ProjectRelationMixin

from .forms import SSHKeyFileUploadForm
from .models import SSHKey
from .tasks import disconnect_oauth_from_project


class KeysMixin(ProjectRelationMixin):
    model = SSHKey
    lookup_url_kwarg = 'key_pk'


class ListKeysView(KeysMixin, ListView, CreateView):  # pylint: disable=too-many-ancestors

    """List all keys for project under Project Admin's dashboard."""

    template_name = 'ssh/keys_list.html'


class DeleteKeysView(SuccessMessageMixin, KeysMixin, DeleteView):  # noqa

    """
    Delete a key for project under Project Admin's dashboard.

    It also deletes the key from the VCS service if this key was added as SSH
    deploy key by us in the VCS service.
    """

    template_name = 'ssh/keys_list.html'
    success_message = 'SSH key was deleted succesfully'

    def get_success_url(self):
        return reverse('projects_keys', args=[self.object.project.slug])

    def post(self, *args, **kwargs):  # pylint: disable=arguments-differ
        # Remove SSH key from service (GitHub/GitLab/Bitbucket) before delete it
        # from the database
        key = self.get_object()
        if key.service_id:
            disconnect_oauth_from_project(key.pk, self.request.user.pk)

        response = super(DeleteKeysView, self).post(*args, **kwargs)
        return response


class GenerateKeysView(KeysMixin, TemplateView):

    """Generate a random private/public key on demand."""

    template_name = 'ssh/keys_generate.html'
    success_message = 'SSH key was generated automatically'

    def get_success_url(self):
        return reverse('projects_keys', args=[self.get_project().slug])

    def post(self, request, *args, **kwargs):
        SSHKey.objects.create(project=self.get_project())
        messages.success(request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


class UploadKeysView(SuccessMessageMixin, KeysMixin, FormView):  # noqa

    """
    Upload a private key from the user's computer.

    Once the key is upload successfully a public key automatically generated
    from this private key and saved as a ``SSHKey`` model instance.
    """

    template_name = 'ssh/keys_upload.html'
    form_class = SSHKeyFileUploadForm
    success_message = 'SSH key was upload successfully'

    def get_success_url(self):
        return reverse('projects_keys', args=[self.get_project().slug])

    def form_valid(self, form):
        response = super(UploadKeysView, self).form_valid(form)
        SSHKey.objects.create_from_string(
            form.cleaned_data['private_key'],
            self.get_project(),
        )
        return response


class DetailKeysView(KeysMixin, DetailView):

    """Detailed ``SSHKey`` model instance under Project Admin's dashboard."""

    template_name = 'ssh/keys_detail.html'
