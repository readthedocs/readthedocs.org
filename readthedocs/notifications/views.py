"""views.py: messages extends"""

from django.http import HttpResponseRedirect
from messages_extends.views import message_mark_read, message_mark_all_read


def _with_redirect(fn):
    redirect_to = request.GET.get('next')
    resp = fn(request, message_id)
    if redirect_to:
        resp = HttpResponseRedirect(redirect_to)
    return resp


notification_dismiss = _with_redirect(message_mark_read)
notification_dismiss_all = _with_redirect(message_mark_all_read)
