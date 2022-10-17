sphinxcontrib-jquery
====================

JQuery will be removed from Sphinx 6.0.0. We can expect 6.0.0 to ship in late 2022. See also:

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

package-name:
  ``sphinxcontrib-jquery``

python package:
  ``sphinxcontrib.jquery``

ownership:
  Read the Docs core team will implement the initial releases of an otherwise community-owned package that lives in https://github.com/sphinx-contrib/jquery

functionality:
  sphinxcontrib-jquery is a Sphinx extension that provides a simple mechanism for other Sphinx extensions and themes to ensure that jQuery is included into the HTML build outputs and loaded in the HTML DOM itself.
  More specifically, the extension ensures that jQuery is loaded exactly once no matter how many themes and extensions that request to include jQuery nor the version of Sphinx.

scope:
  This extension assumes that it's enough to provide a single version of jQuery for all of its dependent extensions and themes.
  As the name implies, this extension is built to handle jQuery only.
  It's not a general asset manager and it's not looking to do dependency resolution of jQuery versions.

Usage
-----

The primary users of this package are
**a) theme and extension developers** and
**b) documentation project owners**.

Theme and extension developers:
  The following 2 steps need to be completed:

  #. A Sphinx theme or extension should depend on the python package ``sphinxcontrib-jquery``.
  #. Calling either ``sphinxcontrib.jquery.add_jquery`` or ``sphinxcontrib.jquery.add_jquery_if_sphinx_lt_6``.

  In addition to this, we recommend extension and theme developers to log to the browser's ``console.error`` in case jQuery isn't found. The log message could for instance say:

    "<package-name> depends on sphinxcontrib-jquery. Please ensure that <package-name>.setup(app) is called or add 'sphinxcontrib-jquery' to your conf.py extensions setting."

Documentation project owners:
  If you are depending on a theme or extension that did not itself address the removal of jQuery from Sphinx, you can patch up your project like this:

  #. Add ``sphinxcontrib-jquery`` to your ``requirements.txt``.
  #. Add ``sphinxcontrib.jquery`` to your ``extensions`` setting in ``conf.py``.


``sphinxcontrib.jquery.add_jquery(app)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adds jQuery no matter what, but at most once.
It's useful for themes and extensions that want jQuery added unconditionally or if they want to handle the conditions themselves.

``sphinxcontrib.jquery.add_jquery_if_sphinx_lt_6(app)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adds jQuery if Sphinx is older than version 6, at most once.
This is recommended for extensions and themes that maintain compatibility of Sphinx before and after version 6.

Adding ``sphinxcontrib.jquery`` to a documentation project's ``conf.extensions`` will call this function.

Release
-------

All releases follow semantic versioning: ``<major>.<minor>.<patch>``

* ``major``: Changes that break existing themes and extensions - we'll aim to only ever have ``1.x.y`` releases!
* ``minor``: Changes that contain jQuery updates or substantial feature additions.
* ``patch``: Bug fixes and added compatibility.

For distributed packages with a longer lifecycle, we propose a loose pinning of the patch and minor versions to allow for future updates, which are likely to happen when jQuery receives security updates.
Example: ``sphinxcontrib-jquery>=1.0.0,<2.0.0`` will include all compatible future releases, including jQuery upgrades.


jQuery version and inclusion
----------------------------

Sphinx has kept relatively up to date with jQuery, and this package intends to follow.
The most recently bundled jQuery version was v3.5.1 and only two releases have happened since: 3.6.0 and 3.6.1.
The 3.6.0 release had a very small backwards incompatibility which illustrates how harmless these upgrades are for the general purpose Sphinx package.

Therefore, we propose to start 1.0.0 at 3.5.1 (the currently shipped version) and subsequently release 3.6.1 as the first update of jQuery as 1.1.0.

The bundled jQuery version will be NPM pre-minified and distributed together with the PyPI package.

The minified jQuery JS file is ultimately included by calling `app.add_js_file <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_js_file>`_, which is passed the following arguments:

.. code:: python

  app.add_js_file(
      get_jquery_url_path(),
      loading_method="defer",
      priority=200,
      integrity="sha256-{}".format(get_jquery_sha256_checksum())
  )
