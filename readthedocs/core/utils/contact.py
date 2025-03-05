import markdown
import structlog
from django.conf import settings
from django.core.mail import send_mail
from django.template import Context
from django.template import Engine


log = structlog.get_logger(__name__)


# TODO: re-implement sending notifications to users.
# This needs more thinking because the notifications where "Generic",
# and now we need to register a  ``Message`` with its ID.
def contact_users(
    users,
    email_subject=None,
    email_content=None,
    from_email=None,
    context_function=None,
    dryrun=True,
):
    """
    Send an email to a list of users.

    :param users: Queryset of Users.
    :param string email_subject: Email subject
    :param string email_content: Email content (markdown)
    :param string from_email: Email to sent from (Test Support <support@test.com>)
    :param context_function: A callable that will receive an user
     and return a dict of additional context to be used in the email content
    :param bool dryrun: If `True` don't sent the email, just logs the content

    The `email_content` contents will be rendered using a template with the following context::

        {
            'user': <user object>,
            'production_uri': https://readthedocs.org,
        }

    :returns: A dictionary with a list of sent/failed emails.
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    context_function = context_function or (lambda user: {})
    sent_emails = set()
    failed_emails = set()

    engine = Engine.get_default()

    email_template = engine.from_string(email_content or "")
    email_txt_template = engine.get_template("core/email/common.txt")
    email_html_template = engine.get_template("core/email/common.html")

    total = users.count()
    for count, user in enumerate(users.iterator(), start=1):
        context = {
            "user": user,
            "production_uri": f"https://{settings.PRODUCTION_DOMAIN}",
        }
        context.update(context_function(user))

        if email_subject:
            emails = list(
                user.emailaddress_set.filter(verified=True)
                .exclude(email=user.email)
                .values_list("email", flat=True)
            )
            emails.append(user.email)

            # First render the markdown context.
            email_txt_content = email_template.render(Context(context))
            email_html_content = markdown.markdown(email_txt_content)

            # Now render it using the base email templates.
            email_txt_rendered = email_txt_template.render(Context({"content": email_txt_content}))
            email_html_rendered = email_html_template.render(
                Context({"content": email_html_content})
            )

            try:
                kwargs = {
                    "subject": email_subject,
                    "message": email_txt_rendered,
                    "html_message": email_html_rendered,
                    "from_email": from_email,
                    "recipient_list": emails,
                }
                if not dryrun:
                    send_mail(**kwargs)
            except Exception:
                log.exception("Email failed to send")
                failed_emails.update(emails)
            else:
                log.info("Email sent.", emails=emails, count=count, total=total)
                sent_emails.update(emails)

    return {
        "email": {
            "sent": sent_emails,
            "failed": failed_emails,
        },
    }
