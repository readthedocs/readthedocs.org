from django.contrib.messages.storage.base import Message
from messages_extends.storages import FallbackStorage
from messages_extends.models import Message as PersistentMessage


class FallbackUniqueStorage(FallbackStorage):

    def process_message(self, message, *args, **kwargs):
        """Queue unique messages by checking the message list for duplicates"""
        persist_messages = (PersistentMessage.objects
                            .filter(message=message.message,
                                    user=self.request.user))
        if persist_messages.exists():
            return
        for storage in self.storages:
            if hasattr(storage, 'process_message'):
                message = storage.process_message(message, *args, **kwargs)
                if not message:
                    return
        self._queued_messages.append(message)

    def add(self, level, message, extra_tags='', *args, **kwargs):
        if not message:
            return
            # Check that the message level is not less than the recording level.
        level = int(level)
        if level < self.level:
            return
            # Add the message
        self.added_new = True
        message = Message(level, message, extra_tags=extra_tags)
        self.process_message(message, *args, **kwargs)
