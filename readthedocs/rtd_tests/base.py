"""Base classes and mixins for unit tests."""
import structlog
from collections import OrderedDict
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

log = structlog.get_logger(__name__)


class RequestFactoryTestMixin:

    """
    Adds helper methods for testing with :py:class:`RequestFactory`

    This handles setting up authentication, messages, and session handling
    """

    def request(self, method, *args, **kwargs):
        """
        Perform request from factory.

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
        fn = getattr(factory, method)
        request = fn(*args, **kwargs)

        # Mock user, session, and messages
        request.user = kwargs.pop("user", AnonymousUser())

        session = kwargs.pop("session", {})
        middleware = SessionMiddleware(lambda request: HttpResponse())
        middleware.process_request(request)
        request.session.update(session)
        request.session.save()

        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        return request


class WizardTestCase(RequestFactoryTestMixin, TestCase):

    """Test case for testing wizard forms."""

    step_data = OrderedDict({})
    url = None
    wizard_class_slug = None
    wizard_class = None

    @patch("readthedocs.core.utils.trigger_build", lambda x: None)
    def post_step(self, step, **kwargs):
        """
        Post step form data to `url`, using supplementary `kwargs`

        Use data from kwargs to build dict to pass into form
        """
        if not self.url:
            raise Exception("Missing wizard URL")
        try:
            data = {
                "{}-{}".format(step, k): v
                for (k, v) in list(self.step_data[step].items())
            }
        except KeyError:
            pass
        # Update with prefixed step data
        data["{}-current_step".format(self.wizard_class_slug)] = step
        view = self.wizard_class.as_view()
        req = self.request("post", self.url, data=data, **kwargs)
        resp = view(req)
        self.assertIsNotNone(resp)
        return resp

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardResponse(self, response, step=None):  # noqa
        """Assert successful wizard response."""
        # This is the last form
        if step is None:
            try:
                wizard = response.context_data["wizard"]
                self.assertEqual(wizard["form"].errors, {})
            except (TypeError, KeyError):
                pass
            self.assertEqual(response.status_code, 302)
        else:
            self.assertIn("wizard", response.context_data)
            wizard = response.context_data["wizard"]
            try:
                self.assertEqual(wizard["form"].errors, {})
            except AssertionError:
                self.assertIsNone(wizard["form"].errors)
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.context_data["wizard"])
            self.assertEqual(wizard["steps"].current, step)
            response.render()
            self.assertContains(
                response,
                'name="{}-current_step"'.format(self.wizard_class_slug),
            )

    # We use camelCase on purpose here to conform with unittest's naming
    # conventions.
    def assertWizardFailure(self, response, field, match=None):  # noqa
        """
        Assert field threw a validation error.

        response
            Client response object

        field
            Field name to test for validation error

        match
            Regex match for field validation error
        """
        self.assertEqual(response.status_code, 200)
        self.assertIn("wizard", response.context_data)
        self.assertIn("form", response.context_data["wizard"])
        self.assertIn(field, response.context_data["wizard"]["form"].errors)
        if match is not None:
            error = response.context_data["wizard"]["form"].errors[field]
            self.assertRegex(str(error), match)  # noqa
