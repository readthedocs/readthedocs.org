from readthedocs.notifications.constants import INFO
from readthedocs.notifications.messages import Message


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
