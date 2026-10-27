from readthedocs.notifications.constants import INFO
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry
from readthedocs.projects.exceptions import RepositoryError


class TestMessage:
    def test_xss_protection(self):
        message = Message(
            id="test",
            header="XSS: {{header}}",
            body="XSS: {{body}}",
            type=INFO,
        )
        message.set_format_values(
            {
                "header": "<p>xss</p>",
                "body": "<span>xss</span>",
            }
        )

        assert message.get_rendered_header() == "XSS: &lt;p&gt;xss&lt;/p&gt;"
        assert message.get_rendered_body() == "XSS: &lt;span&gt;xss&lt;/span&gt;"

    def test_missing_key_format_values(self):
        message = Message(
            id="test",
            header="Missing format value: {{header}}",
            body="Missing format value: {{body}}",
            type=INFO,
        )

        assert message.get_rendered_header() == "Missing format value: "
        assert message.get_rendered_body() == "Missing format value: "

    def test_clone_error_shows_the_git_output_escaped(self):
        message = registry.get(
            RepositoryError.CLONE_ERROR_WITH_OUTPUT,
            format_values={"output": "fatal: couldn't find remote ref <pull/13/head>"},
        )

        body = message.get_rendered_body()
        assert "<pre>fatal: couldn&#x27;t find remote ref &lt;pull/13/head&gt;</pre>" in body
