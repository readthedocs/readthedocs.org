from __future__ import absolute_import
from functools import partial
from mock import Mock
from unittest import TestCase

from readthedocs.restapi.permissions import APIRestrictedPermission


class APIRestrictedPermissionTests(TestCase):
    def get_request(self, method, is_admin):
        request = Mock()
        request.method = method
        request.user.is_staff = is_admin
        return request

    def assertAllow(self, handler, method, is_admin, obj=None):
        if obj is None:
            self.assertTrue(handler.has_permission(
                request=self.get_request(method, is_admin=is_admin),
                view=None))
        else:
            self.assertTrue(handler.has_object_permission(
                request=self.get_request(method, is_admin=is_admin),
                view=None,
                obj=obj))

    def assertDisallow(self, handler, method, is_admin, obj=None):
        if obj is None:
            self.assertFalse(handler.has_permission(
                request=self.get_request(method, is_admin=is_admin),
                view=None))
        else:
            self.assertFalse(handler.has_object_permission(
                request=self.get_request(method, is_admin=is_admin),
                view=None,
                obj=obj))

    def test_non_object_permissions(self):
        handler = APIRestrictedPermission()

        assertAllow = partial(self.assertAllow, handler, obj=None)
        assertDisallow = partial(self.assertDisallow, handler, obj=None)

        assertAllow('GET', is_admin=False)
        assertAllow('HEAD', is_admin=False)
        assertAllow('OPTIONS', is_admin=False)
        assertDisallow('DELETE', is_admin=False)
        assertDisallow('PATCH', is_admin=False)
        assertDisallow('POST', is_admin=False)
        assertDisallow('PUT', is_admin=False)

        assertAllow('GET', is_admin=True)
        assertAllow('HEAD', is_admin=True)
        assertAllow('OPTIONS', is_admin=True)
        assertAllow('DELETE', is_admin=True)
        assertAllow('PATCH', is_admin=True)
        assertAllow('POST', is_admin=True)
        assertAllow('PUT', is_admin=True)

    def test_object_permissions(self):
        handler = APIRestrictedPermission()

        obj = Mock()

        assertAllow = partial(self.assertAllow, handler, obj=obj)
        assertDisallow = partial(self.assertDisallow, handler, obj=obj)

        assertAllow('GET', is_admin=False)
        assertAllow('HEAD', is_admin=False)
        assertAllow('OPTIONS', is_admin=False)
        assertDisallow('DELETE', is_admin=False)
        assertDisallow('PATCH', is_admin=False)
        assertDisallow('POST', is_admin=False)
        assertDisallow('PUT', is_admin=False)

        assertAllow('GET', is_admin=True)
        assertAllow('HEAD', is_admin=True)
        assertAllow('OPTIONS', is_admin=True)
        assertAllow('DELETE', is_admin=True)
        assertAllow('PATCH', is_admin=True)
        assertAllow('POST', is_admin=True)
        assertAllow('PUT', is_admin=True)
