from functools import partial
from unittest import TestCase

from unittest.mock import Mock

from readthedocs.api.v2.permissions import ReadOnlyPermission


class APIRestrictedPermissionTests(TestCase):
    def get_request(self, method, is_admin):
        request = Mock()
        request.method = method
        request.user.is_staff = is_admin
        return request

    def assertAllow(self, handler, method, is_admin, obj=None):
        if obj is None:
            self.assertTrue(
                handler.has_permission(
                    request=self.get_request(method, is_admin=is_admin),
                    view=None,
                )
            )
        else:
            self.assertTrue(
                handler.has_object_permission(
                    request=self.get_request(method, is_admin=is_admin),
                    view=None,
                    obj=obj,
                )
            )

    def assertDisallow(self, handler, method, is_admin, obj=None):
        if obj is None:
            self.assertFalse(
                handler.has_permission(
                    request=self.get_request(method, is_admin=is_admin),
                    view=None,
                )
            )
        else:
            self.assertFalse(
                handler.has_object_permission(
                    request=self.get_request(method, is_admin=is_admin),
                    view=None,
                    obj=obj,
                )
            )

    def test_read_only_permission(self):
        handler = ReadOnlyPermission()

        assertAllow = partial(self.assertAllow, handler, obj=None)
        assertDisallow = partial(self.assertDisallow, handler, obj=None)

        assertAllow("GET", is_admin=False)
        assertAllow("HEAD", is_admin=False)
        assertAllow("OPTIONS", is_admin=False)
        assertDisallow("DELETE", is_admin=False)
        assertDisallow("PATCH", is_admin=False)
        assertDisallow("POST", is_admin=False)
        assertDisallow("PUT", is_admin=False)

        assertAllow("GET", is_admin=True)
        assertAllow("HEAD", is_admin=True)
        assertAllow("OPTIONS", is_admin=True)
        assertDisallow("DELETE", is_admin=True)
        assertDisallow("PATCH", is_admin=True)
        assertDisallow("POST", is_admin=True)
        assertDisallow("PUT", is_admin=True)
