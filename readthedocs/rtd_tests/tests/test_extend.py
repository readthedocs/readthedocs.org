from __future__ import absolute_import
from builtins import object
from django.test import TestCase, override_settings

from readthedocs.core.utils.extend import (SettingsOverrideObject,
                                           get_override_class)


# Top level to ensure module name is correct
class FooBase(object):
    def bar(self):
        return 1

    @classmethod
    def baz(cls):
        return 1


class NewFoo(FooBase):
    def bar(self):
        return 2

    @classmethod
    def baz(cls):
        return 2


EXTEND_PATH = __name__ + '.Foo'
EXTEND_BASE_PATH = __name__ + '.FooBase'
EXTEND_OVERRIDE_PATH = __name__ + '.NewFoo'


class ExtendTests(TestCase):

    @override_settings(FOO_OVERRIDE_CLASS=None)
    def test_no_override(self):
        """Test class without override"""
        class Foo(SettingsOverrideObject):
            _default_class = FooBase
            _override_setting = 'FOO_OVERRIDE_CLASS'

        foo = Foo()
        self.assertEqual(foo.__class__.__name__, 'FooBase')
        self.assertEqual(foo.bar(), 1)
        self.assertEqual(Foo.baz(), 1)

        override_class = get_override_class(Foo, Foo._default_class)
        self.assertEqual(override_class, FooBase)

    @override_settings(FOO_OVERRIDE_CLASS=EXTEND_OVERRIDE_PATH)
    def test_with_basic_override(self):
        """Test class override setting defined"""
        class Foo(SettingsOverrideObject):
            _default_class = FooBase
            _override_setting = 'FOO_OVERRIDE_CLASS'

        foo = Foo()
        self.assertEqual(foo.__class__.__name__, 'NewFoo')
        self.assertEqual(foo.bar(), 2)
        self.assertEqual(Foo.baz(), 2)

        override_class = get_override_class(Foo, Foo._default_class)
        self.assertEqual(override_class, NewFoo)

    @override_settings(FOO_OVERRIDE_CLASS=None,
                       CLASS_OVERRIDES={
                           EXTEND_PATH: EXTEND_OVERRIDE_PATH,
                       })
    def test_with_advanced_override(self):
        """Test class with override using `CLASS_OVERRIDES`"""
        class Foo(SettingsOverrideObject):
            _default_class = FooBase
            _override_setting = 'FOO_OVERRIDE_CLASS'

        foo = Foo()
        self.assertEqual(foo.__class__.__name__, 'NewFoo')
        self.assertEqual(foo.bar(), 2)
        self.assertEqual(Foo.baz(), 2)

        override_class = get_override_class(Foo, Foo._default_class)
        self.assertEqual(override_class, NewFoo)

    @override_settings(FOO_OVERRIDE_CLASS=None,
                       CLASS_OVERRIDES={
                           EXTEND_PATH: EXTEND_OVERRIDE_PATH,
                       })
    def test_with_advanced_override_only(self):
        """Test class with no `override_setting`"""
        class Foo(SettingsOverrideObject):
            _default_class = FooBase

        foo = Foo()
        self.assertEqual(foo.__class__.__name__, 'NewFoo')
        self.assertEqual(foo.bar(), 2)
        self.assertEqual(Foo.baz(), 2)

        override_class = get_override_class(Foo, Foo._default_class)
        self.assertEqual(override_class, NewFoo)
