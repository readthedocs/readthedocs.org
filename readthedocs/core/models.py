from django.db import models
from django.db.models.signals import post_save
from django.db.utils import DatabaseError
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext

STANDARD_EMAIL = "anonymous@readthedocs.org"

class UserProfile (models.Model):
    """Additional information about a User.
    """
    user = models.ForeignKey(User, verbose_name=_('User'), unique=True, related_name='profile')
    whitelisted = models.BooleanField(_('Whitelisted'))
    homepage = models.CharField(_('Homepage'), max_length=100, blank=True)
    allow_email = models.BooleanField(_('Allow email'), help_text=_('Show your email on VCS contributions.'), default=True)

    def __unicode__(self):
        return ugettext("%(username)s's profile") % {'username': self.user.username}

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), {'username': self.user.username})
    get_absolute_url = models.permalink(get_absolute_url)

    def get_contribution_details(self):
        """
        Gets the line to put into commits to attribute the author.

        Returns a tuple (name, email)
        """
        if self.user.first_name and self.user.last_name:
            name = '%s %s' % (self.user.first_name, self.user.last_name)
        else:
            name = self.user.username
        if self.allow_email:
            email = self.user.email
        else:
            email = STANDARD_EMAIL
        return (name, email)


@receiver(post_save, sender=User)
def create_profile(sender, **kwargs):
    if kwargs['created'] is True:
        try:
            UserProfile.objects.create(user_id=kwargs['instance'].id)
        except DatabaseError:
            pass
