How to setup URL redirects for documentation projects
=====================================================

In this guide,
you will learn the steps necessary to configure your Read the Docs project for redirecting visitors from one location to another.

These user-defined redirects are handled at the HTTP-level,
which means that a reader will not notice anything in their browser.
A user visiting the *old URL* will automatically end up at the *new URL*.

.. seealso::

   :doc:`/automatic-redirects`
     The need for a redirect often comes from external links to your documentation.
     Read more about handling links in this explanation of best practices.

   :doc:`/user-defined-redirects`
     If you want to know more about our implementation of redirects,
     you can look up more examples in our reference before continuing with the how-to.

Setting up a redirect
---------------------

Redirects are configured in the project dashboard,
go to :menuselection:`Admin > Redirects`.

.. figure:: /img/screenshot_redirects.png
   :alt: Screenshot of the Redirect admin page
   :scale: 50%
   :align: center

   Navigate to the :guilabel:`Redirect` page and you will see an overview of all active rules.
   In this guide, we go through how to use the :guilabel:`Add Redirect` function.

After navigating to :guilabel:`Add Redirect`,
you need to select a :guilabel:`Redirect Type`.
This is where things get a bit more complicated you need to fill in specific information according to that choice.

Choosing a :guilabel:`Redirect Type`
------------------------------------

There are different types of redirect rules targeting different needs.
For each choice in :guilabel:`Redirect Type`,
you can mark the choice in order to experiment with choices in order to **preview** the final rule generated.

Prefix redirect
  This option is often relevant when moving a project from a former host to Read the Docs.
  In this case, often URL paths hierarchies are redirected.

  Read more about this option in :ref:`user-defined-redirects:Prefix redirects`

Page redirect
  With this option,
  you can specify a page in your documentation to redirect elsewhere.
  The rule triggers no matter the version of your documentation that the user is visiting.
  This rule can also redirect to another website.

  Read more about this option in :ref:`user-defined-redirects:Page redirects`

Exact redirect
  With this option,
  you can specify a page in your documentation to redirect elsewhere.
  The rule is specific to the language and version of your documentation that the user is visiting.
  This rule can also redirect to another website.

  Read more about this option in :ref:`user-defined-redirects:Exact redirects`

Sphinx HTMLDir => HTML
  If you choose to change your Sphinx builder from *DirHTML writer* to the default *html5writer*,
  you can redirect all mismatches automatically.

  Read more about this option in :ref:`user-defined-redirects:Sphinx redirects`

Sphinx HTML => HTMLDir
  Similarly to the former option,
  if you choose to change your Sphinx builder from the default *html5writer* to *DirHTML writer*,
  you can redirect all mismatches automatically.

  Read more about this option in :ref:`user-defined-redirects:Sphinx redirects`

Defining the redirect rule
--------------------------

As mentioned before,
you can pick and choose a :guilabel:`Redirect Type` that fits your redirect need.
When you have entered a :guilabel:`From URL` and :guilabel:`To URL` and the redirect preview looks good,
you are ready to save the rule.

Saving the redirect
-------------------

The redirect is not activated before you click :guilabel:`Save`.
Before clicking, you are free to experiment and preview the effects.
Your redirect rules is added and effective immediately after saving it.

After adding the rule,
you can add more redirects as needed.
There are now immediate upper bounds to how many redirect rules a project may define.

Editing and deleting redirects
------------------------------

You can always revisit :menuselection:`Admin > Redirects`.
in order to delete a rule or edit it.

When editing a rule,
you can change its :guilabel:`Redirect Type` and its :guilabel:`From URL` or :guilabel:`To URL`.
