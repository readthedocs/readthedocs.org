Connecting with an Enterprise Github
====================================

Github integration is provided via the `django-allauth`_ package, and by default connected with `github.com`_.
Next we'll detail how to swap out this connection to use an enterprise edition of Github:

1. Change the social account provider settings to point the Enterprise Github (value of ``{{github_url}}`` in the
   ``local_settings.py``):

    .. code-block:: python

        from .dev import CommunityDevSettings
        _SETTINGS = CommunityDevSettings()

        SOCIALACCOUNT_PROVIDERS = _SETTINGS.SOCIALACCOUNT_PROVIDERS
        SOCIALACCOUNT_PROVIDERS['github']['GITHUB_URL'] == '{{github_url}}'

2. Create an OAuth Github Application by following the `official guide <https://developer.github.com/apps/building-oauth-apps/creating-an-oauth-app/>`_. Note here you must provide the address of the readthedocs
   instance you're setting up. This will give you a Github application ``client id`` and ``secret``.

3. Use these two, plus the domain name of the readthedocs instance to register a site, and a social account provider.
   This could be done from the admin dashboard of readthedocs instance, or by running the following script:

    .. code-block:: python

        # config_github.py
        from __future__ import unicode_literals

        from allauth.socialaccount.providers.github.provider import GitHubProvider
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        from django.conf import settings

        # create a site for the authentication system
        PRODUCTION_DOMAIN = getattr(settings, 'PRODUCTION_DOMAIN')
        SITE_ID = getattr(settings, 'SITE_ID')
        site, _ = Site.objects.update_or_create(id=SITE_ID,
                                                defaults=dict(name=PRODUCTION_DOMAIN,
                                                              domain=PRODUCTION_DOMAIN))

        # change the github social account provider to link to the enterprise Github
        GITHUB_APP_CLIENT_ID = '{{github_app_client_id}}'
        GITHUB_APP_SECRET = '{{github_app_secret}}'
        app, _ = SocialApp.objects.update_or_create(provider=GitHubProvider.id, name='github',
                                                   defaults=dict(client_id=GITHUB_APP_CLIENT_ID,
                                                                 secret=GITHUB_APP_SECRET, key=''))

        app.sites.add(site)  # enable th enterprise Github on the current domain

    Make sure to replace ``{{github_app_client_id}}`` with the Github application client id, and
    ``{{github_app_secret}}`` wit the Github application secret. Then run from a shell:

    .. code-block:: python

        cat config_github.py | python manage.py shell

.. _django-allauth: https://github.com/pennersr/django-allauth
.. _github.com: https://github.com/
