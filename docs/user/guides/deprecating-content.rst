How to deprecate content
========================

When you deprecate a feature from your project,
you may want to deprecate its docs as well,
and stop your users from reading that content.

Deprecating content may sound as easy as delete it,
but doing that will break existing links,
and you don't necessary want to make the content inaccessible.
Here you'll find some tips on how to use Read the Docs to deprecate your content
progressively and in non harmful ways.

.. seealso::

   :doc:`/guides/best-practice/links`
     More information about handling URL structures, renaming and removing content.

Deprecating versions
--------------------

If you have multiple versions of your project,
it makes sense to have its :doc:`documentation versioned </versions>` as well.
For example, if you have the following versions and want to deprecate v1.

- ``https://project.readthedocs.io/en/v1/``
- ``https://project.readthedocs.io/en/v2/``
- ``https://project.readthedocs.io/en/v3/``

For cases like this you can *hide* a version.
Hidden versions won't be listed in the versions menu of your docs,
and they will be listed in a :doc:`robots.txt file </reference/robots>`
to stop search engines of showing results for that version.

Users can still see all versions in the dashboard of your project.
To hide a version go to your project and click on :guilabel:`Versions` > :guilabel:`Edit`,
and mark the :guilabel:`Hidden` option. Check :ref:`versions:Version States` for more information.

.. note::

   If the versions of your project follow the semver_ convention,
   you can activate the :ref:`versions:version warning notifications` option for your project.
   A banner with a warning and linking to the stable version
   will be shown on all versions that are lower than the stable one.

   .. _semver: https://semver.org/

Deprecating pages
-----------------

You may not always want to deprecate a version, but deprecate some pages.
For example, if you have documentation about two APIs and you want to deprecate v1:

- ``https://project.readthedocs.io/en/latest/api/v1.html``
- ``https://project.readthedocs.io/en/latest/api/v2.html``

A simple way is just adding a warning at the top of the page,
this will warn users visiting that page,
but it won't stop users from being redirected to that page from search results.
You can add an entry of that page in a :doc:`custom robots.txt </reference/robots>` file
to avoid search engines of showing those results. For example::

   # robots.txt

   User-agent: *

   Disallow: /en/latest/api/v1.html # Deprecated API

However, your users will still see search results from that page if they use the search from your docs.
With Read the Docs you can set a :ref:`custom rank per pages <config-file/v2:search.ranking>`.
For example:

.. code-block:: yaml

   # .readthedocs.yaml

   version: 2
   search:
      ranking:
         api/v1.html: -1

This won't hide results from that page, but it will give priority to results from other pages.

.. TODO: mention search.ignore when it's implemented.

.. tip::

   You can make use of Sphinx :doc:`directives <sphinx:usage/restructuredtext/directives>`
   (like ``warning``, ``deprecated``, ``versionchanged``)
   or MkDocs `admonitions <https://python-markdown.github.io/extensions/admonition/>`_
   to warn your users about deprecated content.

Moving and deleting pages
-------------------------

After you have deprecated a feature for a while,
you may want to get rid of its documentation,
that's OK, you don't have to maintain that content forever.
However, be aware that users may have links of that page saved,
and it will be frustrating and confusing for them to get a 404.

To solve that problem you can create a redirect to a page with a similar feature/content,
like redirecting to the docs of the v2 of your API when your users visit the deleted docs from v1,
this is a :ref:`page redirect <user-defined-redirects:page redirects>` from ``/api/v1.html`` to ``/api/v2.html``.
See :doc:`/user-defined-redirects`.
