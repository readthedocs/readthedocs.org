import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.models import UserProfile

log = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            log.info("Whitelisting %s" % user)
            try:
                profile = user.get_profile()
                profile.whitelisted = True
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.get_or_create(user=user, whitelisted=True)
