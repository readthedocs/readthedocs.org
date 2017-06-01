"""Base classes and mixins for unit tests."""
from __future__ import absolute_import
from builtins import object
import os
import shutil
import logging
import tempfile
from collections import OrderedDict

from mock import patch
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
import six

log = logging.getLogger(__name__)


class RTDTestCase(TestCase):
    def setUp(self):
        self.original_DOCROOT = settings.DOCROOT
        self.cwd = os.path.dirname(__file__)
        self.build_dir = tempfile.mkdtemp()
        log.info("build dir: %s", self.build_dir)
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        settings.DOCROOT = self.build_dir

    def tearDown(self):
        shutil.rmtree(self.build_dir)
        settings.DOCROOT = self.original_DOCROOT


@patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
@patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
class MockBuildTestCase(TestCase):

    """Mock build triggers for test cases"""

    pass


class RequestFactoryTestMixin(object):

    """Adds helper methods for testing with :py:class:`RequestFactory`

    This handles setting up authentication, messages, and session handling
    """

    def request(self, *args, **kwargs):
        """Perform request from factory

        :param method: Request method as string
        :returns: Request instance

        Several additional keywords arguments can be passed in:

        user
            User instance to use for the request, will default to an
            :py:class:`AnonymousUser` instance otherwise.

        session
            Dictionary to instantiate the session handler with.

        Other keyword arguments are passed into the request method
        """
        factory = RequestFactory()
        method = kwargs.pop('method', 'get')
        fn = getattr(factory, method)
        request = fn(*args, **kwargs)

        # Mock user, session, and messages
        request.user = kwargs.pop('user', AnonymousUser())

        session = kwargs.pop('session', {})
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.update(session)
        request.session.save()

        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        return request


class WizardTestCase(RequestFactoryTestMixin, TestCase):

    """Test case for testing wizard forms"""

    step_data = OrderedDict({})
    url = None
    wizard_class_slug = None
    wizard_class = None

    @patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
    def post_step(self, step, **kwargs):
        """Post step form data to `url`, using supplementary `kwargs`

        Use data from kwargs to build dict to pass into form
        """
        if not self.url:
            raise Exception('Missing wizard URL')
        try:
            data = dict(
                ('{0}-{1}'.format(step, k), v)
                for (k, v) in list(self.step_data[step].items())
            )
        except KeyError:
            pass
        # Update with prefixed step data
        data['{0}-current_step'.format(self.wizard_class_slug)] = step
        view = self.wizard_class.as_view()
        req = self.request(self.url, method='post', data=data, **kwargs)
        resp = view(req)
        self.assertIsNotNone(resp)
        return resp

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardResponse(self, response, step=None):  # noqa
        """Assert successful wizard response"""
        # This is the last form
        if step is None:
            try:
                wizard = response.context_data['wizard']
                self.assertEqual(wizard['form'].errors, {})
            except (TypeError, KeyError):
                pass
            self.assertEqual(response.status_code, 302)
        else:
            self.assertIn('wizard', response.context_data)
            wizard = response.context_data['wizard']
            try:
                self.assertEqual(wizard['form'].errors, {})
            except AssertionError:
                self.assertIsNone(wizard['form'].errors)
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.context_data['wizard'])
            self.assertEqual(wizard['steps'].current, step)
            response.render()
            self.assertContains(
                response,
                u'name="{0}-current_step"'.format(self.wizard_class_slug)
            )

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardFailure(self, response, field, match=None):  # noqa
        """Assert field threw a validation error

        response
            Client response object

        field
            Field name to test for validation error

        match
            Regex match for field validation error
        """
        self.assertEqual(response.status_code, 200)
        self.assertIn('wizard', response.context_data)
        self.assertIn('form', response.context_data['wizard'])
        self.assertIn(field, response.context_data['wizard']['form'].errors)
        if match is not None:
            error = response.context_data['wizard']['form'].errors[field]
            self.assertRegexpMatches(six.text_type(error), match)
