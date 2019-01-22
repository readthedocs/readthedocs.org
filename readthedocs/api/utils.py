# -*- coding: utf-8 -*-

"""Utility classes for api module."""
import logging

from django.utils.translation import ugettext
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource


log = logging.getLogger(__name__)


class PostAuthentication(BasicAuthentication):

    """Require HTTP Basic authentication for any method other than GET."""

    def is_authenticated(self, request, **kwargs):
        val = super().is_authenticated(request, **kwargs)
        if request.method == 'GET':
            return True
        return val


class EnhancedModelResource(ModelResource):

    def obj_get_list(self, request=None, *_, **kwargs):  # noqa
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
        filters = None

        if hasattr(request, 'GET'):
            filters = request.GET

        applicable_filters = self.build_filters(filters=filters)
        applicable_filters.update(kwargs)

        try:
            return self.get_object_list(request).filter(**applicable_filters)
        except ValueError as e:
            raise NotFound(
                ugettext(
                    'Invalid resource lookup data provided '
                    '(mismatched type).: %(error)s',
                ) % {'error': e},
            )


class OwnerAuthorization(Authorization):

    def apply_limits(self, request, object_list):
        if request and hasattr(request, 'user') and request.method != 'GET':
            if request.user.is_authenticated:
                object_list = object_list.filter(users__in=[request.user])
            else:
                object_list = object_list.none()

        return object_list
