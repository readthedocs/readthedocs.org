sphinxcontrib-jquery
====================

jQuery will be removed from Sphinx 6.0.0. We can expect 6.0.0 to ship in late 2022.

.. seealso::

    * https://github.com/sphinx-doc/sphinx/issues/7405
    * https://github.com/sphinx-doc/sphinx/issues/10070
    * https://github.com/readthedocs/sphinx-hoverxref/issues/160
    * https://github.com/readthedocs/sphinx_rtd_theme/issues/1253
    * https://github.com/pydata/pydata-sphinx-theme/issues/764

This is a "request for comments" for a community-owned Sphinx extension that bundles jQuery.


Overview
--------

Comment deadline:
  November 1st, 2022

Package-name:
  ``sphinxcontrib-jquery``

Python package:
  ``sphinxcontrib.jquery``

Dependencies:
  Python 3+, Sphinx 1.8+ (or perhaps no lower bound?)

Ownership:
  Read the Docs core team will implement the initial releases of an otherwise community-owned package that lives in https://github.com/sphinx-contrib/jquery

Functionality:
  sphinxcontrib-jquery is a Sphinx extension that provides a simple mechanism for other Sphinx extensions and themes to ensure that jQuery is included into the HTML build outputs and loaded in the HTML DOM itself.
  More specifically, the extension ensures that jQuery is loaded exactly once no matter how many themes and extensions that request to include jQuery nor the version of Sphinx.

Scope:
  This extension assumes that it's enough to provide a single version of jQuery for all of its dependent extensions and themes.
  As the name implies, this extension is built to handle jQuery only.
  It's not a general asset manager and it's not looking to do dependency resolution of jQuery versions.

Usage
-----

The primary users of this package are
**theme and extension developers** and
**documentation project owners**.


Theme and extension developers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following 2 steps need to be completed:

#. A Sphinx theme or extension should depend on the python package ``sphinxcontrib-jquery``.
#. In your extension's or theme's ``setup(app)``, call ``app.setup_extension("sphinxcontrib.jquery")``.

In addition to this, we recommend extension and theme developers to log to the browser's ``console.error`` in case jQuery isn't found. The log message could for instance say::

  if (typeof $ == "undefined") console.error("<package-name> depends on sphinxcontrib-jquery. Please ensure that <package-name>.setup(app) is called or add 'sphinxcontrib-jquery' to your conf.py extensions setting.")


Documentation project owners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are depending on a theme or extension that did not itself address the removal of jQuery from Sphinx 6, you can patch up your project like this:

#. Add ``sphinxcontrib-jquery`` to your installed dependencies.
#. Add ``sphinxcontrib.jquery`` to your ``extensions`` setting in ``conf.py``.


Calling ``app.setup_extension("sphinxcontrib.jquery")``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a Sphinx theme or extension calls `setup_extension() <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.setup_extension>`_, a call to ``sphinxcontrib.jquery.setup(app)`` will happen. Adding ``sphinxcontrib.jquery`` to a documentation project's ``conf.extensions`` will also call ``sphinxcontrib.jquery.setup(app)`` (at most once).

In ``sphinxcontrib.jquery.setup(app)``, jQuery is added. The default behaviour is to detect the Sphinx version and include jQuery via `app.add_js_file <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_js_file>`__ when Sphinx is from version 6 and up. jQuery is added at most once.


Config value: ``jquery_force_enable``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When setting ``jquery_force_enable=True``, jQuery is added no matter the Sphinx version, but at most once. This is useful if you want to handle alternative conditions for adding jQuery.

.. warning::

  If you set ``jquery_force_enable=True``, you most likely should also add ``Sphinx>=6`` to your theme's/extension's dependencies since versions before this already bundles jQuery!


jQuery version and inclusion
----------------------------

jQuery should be shipped together with the Python package and not be referenced from a CDN.

Sphinx has kept relatively up to date with jQuery, and this package intends to follow.
The most recently bundled jQuery version was v3.5.1 and only two releases have happened since: 3.6.0 and 3.6.1.
The 3.6.0 release had a very small backwards incompatibility which illustrates how harmless these upgrades are for the general purpose Sphinx package.

Therefore, we propose to start the release of ``sphinxcontrib-jquery`` at 3.5.1 (the currently shipped version) and subsequently release 3.6.1 in an update. This will give users that need 3.5.1 a choice of a lower version.

The bundled jQuery version will be NPM pre-minified and distributed together with the PyPI package.

The minified jQuery JS file is ultimately included by calling `app.add_js_file <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_js_file>`__, which is passed the following arguments:

.. code:: python

  app.add_js_file(
      get_jquery_url_path(),
      loading_method="defer",
      priority=200,
      integrity="sha256-{}".format(get_jquery_sha256_checksum()),
  )


.. note:: It's possible to include jQuery in other ways, but this ultimately doesn't require this extension and is therefore not supported.
