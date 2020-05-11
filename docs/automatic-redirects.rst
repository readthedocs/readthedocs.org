Automatic Redirects
===================

Read the Docs supports redirecting certain URLs automatically.
This is an overview of the set of redirects that are fully supported and will work into the future.

Redirecting to a Page
---------------------

You can link to a specific page and have it redirect to your default version.
This is done with the ``/page/`` URL prefix.
You can reach this page by going to https://docs.readthedocs.io/page/automatic-redirects.html.

This allows you to create links that are always up to date.

Another way to handle this is the ``latest`` version.
You can set your ``latest`` version to a specific version and just always link to ``latest``.
You can read more about this in our :doc:`versions </versions>` page.

Root URL
--------

A link to the root of your documentation will redirect to the *default version*,
as set in your project settings.
For example::

    docs.readthedocs.io -> docs.readthedocs.io/en/latest/
    www.pip-installer.org -> www.pip-installer.org/en/latest/

This only works for the root URL, not for internal pages. It's designed to redirect people from http://pip.readthedocs.io/ to the default version of your documentation, since serving up a 404 here would be a pretty terrible user experience. (If your "develop" branch was designated as your default version, then it would redirect to http://pip.readthedocs.io/en/develop.) But, it's not a universal redirecting solution. So, for example, a link to an internal page like http://pip.readthedocs.io/usage.html doesn't redirect to http://pip.readthedocs.io/en/latest/usage.html.

The reasoning behind this is that RTD organizes the URLs for docs so that multiple translations and multiple versions of your docs can be organized logically and consistently for all projects that RTD hosts. For the way that RTD views docs, http://pip.readthedocs.io/en/latest/ is the root directory for your default documentation in English, not http://pip.readthedocs.io/. Just like http://pip.readthedocs.io/en/develop/ is the root for your development documentation in English.

Among all the multiple versions of docs, you can choose which is the "default" version for RTD to display, which usually corresponds to the git branch of the most recent official release from your project.

rtfd.io
~~~~~~~~

Links to rtfd.io are treated the same way as above.
They redirect the root URL to the default version of the project.
They are intended to be easy and short for people to type.

You can reach these docs at https://docs.rtfd.io.

Supported Top-Level Redirects
-----------------------------

.. note:: These "implicit" redirects are supported for legacy reasons.
          We will not be adding support for any more magic redirects.
          If you want additional redirects,
          they should live at a prefix like `Redirecting to a Page`_

The main challenge of URL routing in Read the Docs is handling redirects correctly. Both in the interest of redirecting older URLs that are now obsolete, and in the interest of handling "logical-looking" URLs (leaving out the lang_slug or version_slug shouldn't result in a 404), the following redirects are supported::

    /          -> /en/latest/
    /en/       -> /en/latest/
    /latest/   -> /en/latest/

The language redirect will work for any of the defined ``LANGUAGE_CODES`` we support.
The version redirect will work for supported versions.
