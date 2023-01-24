How to define URL redirects for documentation projects
======================================================

In this guide,
you will learn the steps necessary to configure your Read the Docs project for redirecting visitors from one location to another.

This is done at the HTTP-level,
which means that a reader will not notice anything in their browser.
The user will visit a long to the *old location* and automatically end up at the *new location*.

.. seealso::

   :doc:`/automatic-redirects`
     The need for a redirect often comes from external links to your documentation.
     Read more about handling links in this explanation of best practices.

   :doc:`/user-defined-redirects`
     If you want to know more about our implementation of redirects,
     you should read the reference before continuing with the how-to.

Setting up a redirect
---------------------

Redirects are configured in the project dashboard,
go to :guilabel:`Admin`, then :guilabel:`Redirects`.

.. figure:: /img/screenshot_redirects.png
   :alt: Screenshot of the Redirect admin page
   :scale: 50%
   :align: center

   Navigate to the :guilabel:`Redirect` page and you will see an overview of all active rules.
   In this guide, we go through how to use the :guilabel:`Add Redirect` function.

After navigating to :guilabel:`Add Redirect`,
you need to select a :guilabel:`Redirect Type`.
This is where things get a bit more complicated you need to fill in specific information according to that choice.

Prefix redirect
  Moving a documentation from a former host often means to create prefixed redirects.

  Specifying ``/dev`` adds the following redirect rule:

  .. code-block:: text

    /dev/<any-page-name> => /en/latest/<any-page-name>


Page redirect
  TBD

Exact redirect
  TBD

Sphinx HTMLDir => HTML
  TBD

Sphinx HTML => HTMLDir
  TBD
