.. old reference

.. _Automatic Redirects:

Best practices for linking to your documentation
================================================

Once you start to publish documentation,
external sources will inevitably link to specific pages in your documentation.

Sources of incoming links vary greatly depending on the type of documentation project that is published.
They can include everything from old emails to GitHub issues, wiki articles, software comments, PDF publications, or StackOverflow answers.
Most of these incoming sources are not in your control.

Read the Docs makes it easier to create and manage incoming links by redirecting certain URLs automatically
and giving you access to define your own redirects.

In this article,
we explain how our built-in redirects work and what we consider "best practice" for managing incoming links.

.. seealso::

   :doc:`/versions`
     Read more about how to handle versioned documentation and URL structures.

   :doc:`/user-defined-redirects`
     Overview of all the redirect features available on Read the Docs.
     Many of the redirect features are useful either for building external links or handling requests to old URLs.

   :doc:`/guides/redirects`
     How to add a user-defined redirect, step-by-step.
     Useful if your content changes location!


Best practice: "permalink" your pages
-------------------------------------

You might be familiar with the concept of `permalinks`_ from blogging.
The idea is that a blog post receives a unique link as soon as it's published and that the link does not change afterward.
Incoming sources can reference the blog post even though the blog changes structure or the post title changes.

When creating an external link to a specific documentation page,
chances are that the page is moved as the documentation changes over time.

How should a permalink look for a documentation project?
Firstly, you should know that a *permalink* does not really exist in documentation but it is the result of careful actions to avoid breaking incoming links.

As a documentation owner,
you most likely want users clicking on incoming links to see the latest version of the page.

.. _permalinks: https://en.wikipedia.org/wiki/Permalink

Good practice ✅
~~~~~~~~~~~~~~~~

* Use :ref:`page redirects <user-defined-redirects:Page redirects>` if you are linking to the page in the :term:`default version` of the default language. This allows links to continue working even if those defaults change.
* If you move a page that likely has incoming references, :doc:`create a custom redirect rule </guides/redirects>`.
* Links to other Sphinx projects should use :doc:`intersphinx </guides/intersphinx>`.
* Use minimal filenames that don't require renaming often.
* When possible,
  keep original file names rather than going for low-impact URL renaming.
  Renaming an article's title is great for the reader and great for SEO,
  but this does not have to involve the URL.
* Establish your understanding of the *latest* and :term:`default version` of your documentation at the beginning. Changing their meaning is disruptive to incoming links.
* Keep development versions :ref:`hidden <versions:Version states>` so people do not find them on search engines by mistake.
  This is the best way to ensure that nobody links to URLs that are intended for development purposes.
* Use a :ref:`version warning notifications <versions:Version warning notifications>` to ensure the reader is aware in case they are reading an old (archived) version.

.. tip::

   Using Sphinx?
     If you are using ``:ref:`` for :doc:`cross-referencing </guides/cross-referencing-with-sphinx>`, you may add as many reference labels to a headline as you need,
     keeping old reference labels. This will make refactoring documentation easier and avoid that external projects
     referencing your documentation through :doc:`intersphinx </guides/intersphinx>` break.

Questionable practice 🟡
~~~~~~~~~~~~~~~~~~~~~~~~

* Avoid using specific versions in links unless users need that exact version.
  Versions get outdated.
* Avoid using a public ``latest`` for development versions and do not make your *default version* a development branch.
  Publishing development branches can mean that users are reading instructions for unreleased software or draft documentation.

.. tip::

   404 pages are also okay!
     If documentation pages have been removed or moved,
     it can make the maintainer of the referring website aware that they need to update their link.
     Users will be aware that the documentation **project** still exists but has changed.

     The default Read the Docs 404 page is designed to be helpful,
     but you can also design your own, see :doc:`/reference/404-not-found`.
