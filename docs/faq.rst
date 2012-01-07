Frequently Asked Questions
==========================

My project isn't building with autodoc
--------------------------------------

First, you should check out the Builds tab of your project. That records all of the build attempts that RTD has made to build your project. If you look at your build page, and you see problems with import errors, it's likely that you aren't whitelisted. Virtualenv and pip options won't work without being whitelisted.

You can check whether your account is whitelisted by going to your profile page. That is located at http://readthedocs.org/profiles/YOUR_USERNAME/.

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
            return Mock() if name not in ('__file__', '__path__') else '/dev/null'

    MOCK_MODULES = ['pygtk', 'gtk', 'gobject', 'argparse']
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = Mock()

Of course, replacing `MOCK_MODULES` with the modules that you want to mock out.

Where do I need to put my docs for RTD to find it?
--------------------------------------------------

Read the Docs will crawl your project looking for a ``conf.py``. Where it finds the ``conf.py``, it will run ``sphinx-build`` in that directory. So as long as you only have one set of sphinx documentation in your project, it should Just Work.
