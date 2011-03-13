from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.models import UserProfile
from projects import tasks
from projects.models import Project

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for user in User.objects.filter(profile__whitelisted=False):
            print "Whitelisting %s" % user
            UserProfile.objects.create(user=user, whitelisted=True)
