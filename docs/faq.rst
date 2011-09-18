Frequently Asked Questions
==========================

My project isn't building with autodoc
--------------------------------------

To keep our servers more secure, we white list accounts to allow them to execute code on our servers. If you need autodoc or other custom conf.py code execution options, feel free to Contact Us either in IRC at #readthedocs, or by email at eric@ericholscher.com.


I get import errors on librarires that depend on C modules
----------------------------------------------------------

This happens because our build system doesn't have the dependencies for building your project. This happens with things like libevent and mysql, and other python things that depend on C libraries. We can't support installing random C binaries on our system, so there is another way to fix these imports.

You can mock out the imports for these modules in your conf.py with the following snippet::

    import sys

    class Mock(object):
        def __init__(self, *args):
            pass

        def __getattr__(self, name):
            return Mock

    MOCK_MODULES = ['pygtk', 'gtk', 'gobject', 'argparse']
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = Mock()

Of course, replacing `MOCK_MODULES` with the modules that you want to mock out.
