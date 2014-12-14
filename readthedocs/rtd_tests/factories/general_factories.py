import factory
from django.contrib.auth.models import User


class UserFactory(factory.Factory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'joe %s' % n) 


    @classmethod
    def _prepare(cls, create, password="password_sentinel", **kwargs):
        '''
        Lets user pass password as they might if they use the Django ORM.
        If they don't, the sentinel passes.
        '''
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        user.set_password(password)

        if create:
            user.save()

        return user
