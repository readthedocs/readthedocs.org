Customizing your install
========================

Read the Docs has a lot of :doc:`/settings` that help customize your install.
This document will outline some of the more useful ways that these can be combined.

Have a local settings file
--------------------------

If you put a file named ``local_settings.py`` in the ``readthedocs/settings`` directory, it will override settings available in the base install.

Adding your own logo
--------------------

This requires 2 parts of setup. First, you need to add a custom :setting:`TEMPLATE_DIRS` setting that points at your template overrides. Then, in those template overrides you have to insert your logo where the normal RTD logo goes.

Example ``local_settings.py``::

    import os

    # Directory that the project lives in, aka ../..
    SITE_ROOT = '/'.join(os.path.dirname(__file__).split('/')[0:-2])

    TEMPLATE_DIRS = (
        "%s/var/custom_templates/" % SITE_ROOT, # Your custom template directory, before the RTD one to override it.
        '%s/readthedocs/templates/' % SITE_ROOT, # Default RTD template dir
    )

Example ``base.html`` in your template overrides::

    {% extends "/home/docs/checkouts/readthedocs.org/readthedocs/templates/base.html" %}
    {% load i18n %}

    {% block branding %}{% trans "My sweet site" %} {% endblock %}

You can of course override any block in the template. If there is something that you would like to be able to customize, but isn't currently in a block, please `submit an issue`_.


.. _submit an issue: https://github.com/rtfd/readthedocs.org/issues?sort=created&state=open
