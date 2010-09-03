from django.db import models
from django.contrib.auth.models import User

class UserProfile (models.Model):
    """Additional information about a User.
    """
    user = models.ForeignKey(User, unique=True, related_name='profile')
    whitelisted = models.BooleanField()
    homepage = models.CharField(max_length=100)

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), {'username': self.user.username})
    get_absolute_url = models.permalink(get_absolute_url)

    def __unicode__(self):
        return "%s's profile" % self.user.username

