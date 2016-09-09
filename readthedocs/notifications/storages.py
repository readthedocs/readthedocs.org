from django.contrib.messages.storage.base import Message
from messages_extends.storages import FallbackStorage
from messages_extends.models import Message as PersistentMessage


class FallbackUniqueStorage(FallbackStorage):

    def add(self, level, message, extra_tags='', *args, **kwargs):
        persist_messages = (PersistentMessage.objects
                            .filter(message=message,
                                    user=self.request.user))
        if persist_messages.exists():
            return
        super(FallbackUniqueStorage, self).add(level, message, extra_tags,
                                               *args, **kwargs)
