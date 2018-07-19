# -*- coding: utf-8 -*-
"""Rest API endpoints for SSH application."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging

from django.shortcuts import get_object_or_404
from rest_framework import decorators
from rest_framework.response import Response

from readthedocs.projects.models import Project
from readthedocs.restapi.views.model_views import ProjectViewSet

from .serializers import SSHKeyAdminSerializer, SSHKeySerializer


log = logging.getLogger(__name__)


class ProjectSSHKeyViewSet(ProjectViewSet):

    """
    List SSH project keys.

    This class is an extension to add the ``keys`` endpoint into
    ``readthedocs.restapi.views.model_views.ProjectViewSet``.
    """

    @decorators.detail_route()
    def keys(self, request, **kwargs):
        if request.user.is_superuser:
            project = get_object_or_404(Project.objects.all(), pk=kwargs['pk'])
        else:
            # TODO: check this line from corporate site since I had to remove
            # the ``include_all=True`` that was used here
            project = get_object_or_404(Project.objects.for_admin_user(
                self.request.user), pk=kwargs['pk'],
            )

        ret = []
        for key in project.sshkeys.all():
            data = {
                'public_key': key.public_key,
            }
            if request.user.is_superuser:
                serializer_class = SSHKeyAdminSerializer
            else:
                serializer_class = SSHKeySerializer

            ret.append(serializer_class(key).data)

        return Response(ret)
