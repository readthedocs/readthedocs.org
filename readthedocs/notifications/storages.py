"""Customised storage for notifications."""

from __future__ import absolute_import
from django.contrib.messages.storage.base import Message
from django.utils.safestring import mark_safe
from messages_extends.storages import FallbackStorage
from messages_extends.models import Message as PersistentMessage
from messages_extends.constants import PERSISTENT_MESSAGE_LEVELS


class FallbackUniqueStorage(FallbackStorage):

    """Persistent message fallback storage, but only stores unique notifications

    This loops through all backends to find messages to store, but will skip
    this step if the message already exists for the user in the database.

    Deduplication is important here, as a persistent message may ask a user to
    perform a specific action, such as change a build option.  Duplicated
    messages would lead to confusing UX, where a duplicate message may not be
    dismissed when the prescribed action is taken.  Instead of detecting
    duplication while triggering the message, we handle this at the storage
    level.

    This class also assumes that notifications set as persistent messages are
    more likely to have HTML that should be marked safe. If the level matches a
    persistent message level, mark the message text as safe so that we can
    render the text in templates.
    """

    def _get(self, *args, **kwargs):
        # The database backend for persistent messages doesn't support setting
        # messages with ``mark_safe``, therefore, we need to do it broadly here.
        messages, all_ret = (super(FallbackUniqueStorage, self)
                             ._get(self, *args, **kwargs))
        safe_messages = []
        for message in messages:
            # Handle all message types, if the message is persistent, take
            # special action. As the default message handler, this will also
            # process ephemeral messages
            if message.level in PERSISTENT_MESSAGE_LEVELS:
                message_pk = message.pk
                message = Message(message.level,
                                  mark_safe(message.message),
                                  message.extra_tags)
                message.pk = message_pk
            safe_messages.append(message)
        return safe_messages, all_ret

    def add(self, level, message, extra_tags='', *args, **kwargs):
        user = kwargs.get('user') or self.request.user
        if not user.is_anonymous():
            persist_messages = (PersistentMessage.objects
                                .filter(message=message,
                                        user=user,
                                        read=False))
            if persist_messages.exists():
                return
        super(FallbackUniqueStorage, self).add(level, message, extra_tags,
                                               *args, **kwargs)
