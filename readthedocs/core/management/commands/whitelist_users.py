from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from core.models import UserProfile

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            print _("Acting on ")+'%s' % user
            try:
                profile = user.get_profile()
                profile.whitelisted = True
                profile.save()
            except:
                UserProfile.objects.get_or_create(user=user, whitelisted=True)
