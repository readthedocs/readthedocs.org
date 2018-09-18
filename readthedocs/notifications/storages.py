# -*- coding: utf-8 -*-
"""Customised storage for notifications."""

from __future__ import absolute_import
from django.contrib.messages.storage.base import Message
from django.db.models import Q
from django.utils.safestring import mark_safe
from messages_extends.storages import FallbackStorage, PersistentStorage
from messages_extends.models import Message as PersistentMessage
from messages_extends.constants import PERSISTENT_MESSAGE_LEVELS

try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone

from .constants import NON_PERSISTENT_MESSAGE_LEVELS


class FallbackUniqueStorage(FallbackStorage):

    """
    Persistent message fallback storage, but only stores unique notifications.

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

    storages_names = (
        'readthedocs.notifications.storages.NonPersistentStorage',
        'messages_extends.storages.StickyStorage',
        'messages_extends.storages.PersistentStorage',
        'django.contrib.messages.storage.cookie.CookieStorage',
        'django.contrib.messages.storage.session.SessionStorage',
    )

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
            if message.level in PERSISTENT_MESSAGE_LEVELS + NON_PERSISTENT_MESSAGE_LEVELS:
                message_pk = message.pk
                message = Message(message.level,
                                  mark_safe(message.message),
                                  message.extra_tags)
                message.pk = message_pk
            safe_messages.append(message)
        return safe_messages, all_ret

    def add(self, level, message, extra_tags='', *args, **kwargs):  # noqa
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


class NonPersistentStorage(PersistentStorage):

    """
    Save one time (non-pesistent) messages in the database.

    Messages are saved into the database. ``user`` object is mandatory but
    ``request`` is needed.
    """

    # Non-persistent level numbers start at 100 and it's used to check if it's
    # an actionable message or not
    level = 100

    def _message_queryset(self, include_read=False):
        """Return a queryset of non persistent messages for the request user."""
        expire = timezone.now()

        qs = PersistentMessage.objects.\
            filter(user=self.get_user()).\
            filter(Q(expires=None) | Q(expires__gt=expire)).\
            filter(level__in=NON_PERSISTENT_MESSAGE_LEVELS)
        if not include_read:
            qs = qs.exclude(read=True)

        # We need to save the objects returned by the query before updating it,
        # otherwise they are marked as ``read`` and not returned when executed
        result = list(qs)

        # Mark non-persistent messages as read when show them
        qs.update(read=True)

        return result

    # These methods (_store, process_message) are copied from
    # https://github.com/AliLozano/django-messages-extends/blob/master/messages_extends/storages.py
    # and replaced PERSISTENT_MESSAGE_LEVELS by NON_PERSISTENT_MESSAGE_LEVELS

    def _store(self, messages, response, *args, **kwargs):
        # There are already saved.
        return [
            message for message in messages
            if message.level not in NON_PERSISTENT_MESSAGE_LEVELS
        ]

    def process_message(self, message, *args, **kwargs):
        """
        Convert messages to models and save them.

        If its level is into non-persistent levels, convert the message to
        models and save it
        """
        if message.level not in NON_PERSISTENT_MESSAGE_LEVELS:
            return message

        user = kwargs.get("user") or self.get_user()

        try:
            anonymous = user.is_anonymous()
        except TypeError:
            anonymous = user.is_anonymous
        if anonymous:
            raise NotImplementedError(
                'Persistent message levels cannot be used for anonymous users.')
        message_persistent = PersistentMessage()
        message_persistent.level = message.level
        message_persistent.message = message.message
        message_persistent.extra_tags = message.extra_tags
        message_persistent.user = user

        if "expires" in kwargs:
            message_persistent.expires = kwargs["expires"]
        message_persistent.save()
        return None
