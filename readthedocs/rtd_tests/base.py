import os
import shutil
import logging
from collections import OrderedDict

from mock import patch
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

log = logging.getLogger(__name__)


class RTDTestCase(TestCase):
    def setUp(self):
        self.original_DOCROOT = settings.DOCROOT
        self.cwd = os.path.dirname(__file__)
        self.build_dir = os.path.join(self.cwd, 'builds')
        log.info("build dir: %s" % self.build_dir)
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)
        settings.DOCROOT = self.build_dir

    def tearDown(self):
        shutil.rmtree(self.build_dir)
        settings.DOCROOT = self.original_DOCROOT


@patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
@patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
class MockBuildTestCase(TestCase):
    '''Mock build triggers for test cases'''
    pass


class WizardTestCase(TestCase):
    '''Test case for testing wizard forms'''

    step_data = OrderedDict({})
    url = None
    wizard_class_slug = None

    @patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
    @patch('readthedocs.projects.views.private.trigger_build', lambda x, basic: None)
    def post_step(self, step, **data):
        '''Post step form data to `url`, using supplementary `kwargs`

        Use data from kwargs to build dict to pass into form
        '''
        if not self.url:
            raise Exception('Missing wizard URL')
        try:
            data = {}
            for key in self.step_data:
                data.update({('{0}-{1}'.format(key, k), v)
                             for (k, v) in self.step_data[key].items()})
                if key == step:
                    break
        except KeyError:
            pass
        # Update with prefixed step data
        data['{0}-current_step'.format(self.wizard_class_slug)] = step
        resp = self.client.post(self.url, data)
        self.assertIsNotNone(resp)
        return resp

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardResponse(self, response, step=None):  # noqa
        '''Assert successful wizard response'''
        # Is is the last form
        if step is None:
            try:
                wizard = response.context['wizard']
                self.assertEqual(wizard['form'].errors, {})
            except (TypeError, KeyError):
                pass
            self.assertEqual(response.status_code, 302)
        else:
            self.assertIn('wizard', response.context)
            wizard = response.context['wizard']
            try:
                self.assertEqual(wizard['form'].errors, {})
            except AssertionError:
                self.assertIsNone(wizard['form'].errors)
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.context['wizard'])
            self.assertEqual(wizard['steps'].current, step)
            self.assertIn('{0}-current_step'.format(self.wizard_class_slug),
                          response.content)

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardFailure(self, response, field, match=None):  # noqa
        '''Assert field threw a validation error

        response
            Client response object

        field
            Field name to test for validation error

        match
            Regex match for field validation error
        '''
        self.assertEqual(response.status_code, 200)
        self.assertIn('wizard', response.context)
        self.assertIn('form', response.context['wizard'])
        self.assertIn(field, response.context['wizard']['form'].errors)
        if match is not None:
            error = response.context['wizard']['form'].errors[field]
            self.assertRegexpMatches(unicode(error), match)


class RequestFactoryTestMixin(object):

    """Adds helper methods for testing with :py:cls:`RequestFactory`

    This handles setting up authentication, messages, and session handling
    """

    def request(self, *args, **kwargs):
        """Perform request from factory

        :param method: Request method as string
        :returns: Request instance

        Several additional keywords arguments can be passed in:

        user
            User instance to use for the request, will default to an
            :py:cls:`AnonymousUser` instance otherwise.

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

        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        return request
