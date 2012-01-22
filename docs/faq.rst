Frequently Asked Questions
==========================

My project isn't building with autodoc
--------------------------------------

First, you should check out the Builds tab of your project. That records all of the build attempts that RTD has made to build your project. 

If you need autodoc or other custom options, feel free to Contact Us either in IRC at #readthedocs on Freenode (`http://chat.freenode.net <http://webchat.freenode.net>`_), or by emailing the mailling list.

Mailing list archives are available at http://librelist.com/browser/readthedocs/. To join, send an email to readthedocs@librelist.com, that will allow you to join, then send another mail with the content to post to the list.


How do I change behavior for Read the Docs
-------------------------------------------

When RTD builds your project, it sets the `READTHEDOCS` environment variable to the string `True`. So within your Sphinx's conf.py file, you can vary the behavior based on this. For example::

    import os
    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
    if on_rtd:
        html_theme = 'default'
    else:
        html_theme = 'nature'

I get import errors on libraries that depend on C modules
----------------------------------------------------------

This happens because our build system doesn't have the dependencies for building your project. This happens with things like libevent and mysql, and other python things that depend on C libraries. We can't support installing random C binaries on our system, so there is another way to fix these imports.

You can mock out the imports for these modules in your conf.py with the following snippet::

    import sys

    class Mock(object):
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return Mock()

        @classmethod
        def __getattr__(self, name):
            if name in ('__file__', '__path__'):
                return '/dev/null'
            elif name[0] == name[0].upper():
                return type(name, (), {})
            else:
                return Mock()

    MOCK_MODULES = ['pygtk', 'gtk', 'gobject', 'argparse']
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = Mock()

Of course, replacing `MOCK_MODULES` with the modules that you want to mock out.

Where do I need to put my docs for RTD to find it?
--------------------------------------------------

Read the Docs will crawl your project looking for a ``conf.py``. Where it finds the ``conf.py``, it will run ``sphinx-build`` in that directory. So as long as you only have one set of sphinx documentation in your project, it should Just Work.

I want to use the Blue/Default Sphinx theme
-------------------------------------------

We think that our theme is badass, and better than the default for many reasons. Some people don't like change though :), so there is a hack that will let you keep using the default theme. If you set the ``html_style`` variable in your ``conf.py``, it should default to using the default theme. The value of this doesn't matter, and can be set to None, ``'static/``.
