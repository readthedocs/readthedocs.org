Documentation style guide
=========================

This document will serve as the canonical place to define how we write documentation at Read the Docs.
The goal is to have a shared understanding of how things are done,
and document the conventions that we follow.

Let us know if you have any questions or something isn't clear.

The brand
---------

We are called **Read the Docs**.
The ``the`` is not capitalized.

We do however use the acronym **RTD**.

Titles
------

For page titles we use sentence case.
This means only proper nouns and the first word are capitalized::

    # Good ✅
    How we handle support on Read the Docs.

    # Bad 🔴
    How we Handle Support on Read the Docs

If the page includes multiple sub-headings (H2, H3),
we use sentence case there as well.

Content
-------

* Use ``:menuselection:`` when referring to an item or sequence of items in navigation.
* Use ``:guilabel:`` when referring to a visual element on the screen - such as a button, drop down or input field.
* Use ``**bold text**`` when referring to a non-interactive text element, such as a header.
* Do not break the content across multiple lines at 80 characters,
  but rather break them on semantic meaning (e.g. periods or commas).
  Read more about this `here <https://rhodesmill.org/brandon/2012/one-sentence-per-line/>`_.
* If you are :ref:`cross-referencing <style-guide:Cross-references>` to a different page within our website,
  use the ``doc`` role and not a hyperlink.
* If you are :ref:`cross-referencing <style-guide:Cross-references>` to a section within our website,
  use the ``ref`` role with the label from the `autosectionlabel extension <http://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html>`__.
* Use ``<abstract concept>`` and ``<variable>`` as placeholders in code and URLs. For instance:

  * ``https://<slug>.readthedocs.io``
  * ``:guilabel:`<your username>` dropdown``
* Make sure that **all bullet list items end with a period**, and don't mix periods with no periods.

Linting
~~~~~~~

ReStructuredText for both the RTD user documentation and this developer documentation is linted with `pre-commit` for broken links,
whitespace consistency, and other minor issues.

You can fix many linting issues automatically by installing and running `pre-commit` locally.
To run it on content you have already committed, use the ``--from-ref`` and ``--to-ref`` `flags <https://pre-commit.com/#pre-commit-run>`__.

.. code-block:: bash

   pre-commit run --from-ref <OLDER_COMMIT> --to-ref <RECENT_COMMIT>

Or use ``pre-commit run --all-files`` to lint all files.

Word list
---------

We have a specific way that we write common words:

* ``build command`` is the name of each step in the file.
  We try to avoid confusion with pipelines, jobs and steps from other CIs,
  as we do not have a multi-dimentional build sequence.
* ``build job`` is the name of the general and pre-defined steps that can be overridden.
  They are similar to "steps" in pipelines,
  but on Read the Docs they are pre-defined.
  So it's important to have a unique name.
* ``Git`` should be upper case. Except when referring to the :program:`git` command, then it should be written as `:program:\`git\``.
* ``Git repository`` for the place that stores Git repos. We used to use ``VCS``, but this is deprecated.
* ``Git provider`` for generic references to GitHub/Bitbucket/GitLab/Gitea etc.
  We avoid "host" and "platform" because they are slightly more ambiguous.
* ``how to`` do the thing is explained in a ``how-to guide`` (notice hyphen and spaces).
* ``lifecycle`` is spelled without hyphen nor space.
* ``open source`` should be lower case, unless you are definitely referring to `OSI's Open Source Definition <https://opensource.org/osd>`.
* ``.readthedocs.yaml`` is the general name of the build configuration file.
  Even though we allow custom paths to the config file,
  we only validate ``.readthedocs.yaml`` as the file name.
  Older variations of the name are considered legacy.
  We do not refer to it in general terms.

Substitutions
-------------

The following substitutions are used in our documentation to guarantee consistency and make it easy to apply future changes.

* ``|org_brand|`` is used for mentioning of .org: Example: |org_brand|
* ``|com_brand|`` is used for mentioning of .com. Example: |com_brand|
* ``|git_providers_and|`` is used to mention currently support Git providers with "and". Example: |git_providers_and|
* ``|git_providers_or|`` is used to mention currently support Git providers with "or". Example: |git_providers_or|

Glossary
--------

Since the above Word List is for internal reference,
we also maintain a :doc:`rtd:glossary` with terms that have canonical definitions in our docs.
Terms that can otherwise have multiple definitions
*or* have a particular meaning in Read the Docs context
should always be added to the :doc:`rtd:glossary` and referenced using the ``:term:`` role.

Using a glossary helps us (authors) to have consistent definitions
but even more importantly,
it helps and includes readers by giving them quick and easy access to terms that they may be unfamiliar with.

Use an external link or Intersphinx reference when a term is clearly defined elsewhere.

Cross-references
----------------

Cross-references are great to have as :ref:`inline links <style-guide:Cross-references>`.
Because of sphinx-hoverxref_,
inline links also have a nice tooltip displayed.

We like to cross-reference other articles with a definition list inside a ``seealso::`` admonition box.
It looks like this:

.. code-block:: rst

   .. seealso::

      :doc:`/other/documentation/article`
        You can learn more about <concept> in this (how-to/description/section/article)

.. _sphinx-hoverxref: https://sphinx-hoverxref.readthedocs.io/


Differentiating .org and .com
-----------------------------

When there are differences on .org and .com,
you can use a ``note::`` admonition box with a definition list.
Notice the use of :ref:`substitutions <style-guide:Substitutions>` in the example:

.. code-block:: rst

   .. note::

      |org_brand|
         You need to be *maintainer* of a subproject in order to choose it from your main project.

      |com_brand|
         You need to have *admin access* to the subproject in order to choose it from your main project.

If the contents aren't suitable for a ``note::``, you can also use ``tabs::``.
We are using `sphinx-tabs`_,
however since `sphinx-design`_ also provides tabs,
it should be noted that we don't use that feature of sphinx-design.

.. _sphinx-tabs: https://github.com/executablebooks/sphinx-tabs/
.. _sphinx-design: https://github.com/executablebooks/sphinx-design/


Headlines
---------

Sphinx is very relaxed about how headlines are applied and will digest different notations.
We try to stick to the following:

.. code-block:: rst

   Header 1
   ========

   Header 2
   --------

   Header 3
   ~~~~~~~~

   Header 4
   ^^^^^^^^

In the above, ``Header 1`` is the title of the article.

Diátaxis Framework
------------------

We apply the methodology and concepts of the Diátaxis Framework.
This means that *both content and navigation path* for all sections should fit a single category of the 4 Diátaxis categories:

* Tutorial
* Explanation
* How-to
* Reference

.. seealso::

   `https://diataxis.fr/ <https://diataxis.fr/>`__
     The official website of Diátaxis is the main resource.
     It's best to check this out before guessing what the 4 categories mean.

.. warning:: **Avoid minimal changes**

   If your change has a high coherence with another proposed or planned change,
   propose the changes in the same PR.

   By multi-tasking on several articles about the same topic,
   such as an explanation *and* a how-to,
   you can easily design your content to end up in the right place *Diátaxis-wise*.
   This is great for the author and the reviewers
   and it saves coordination work.

   Minimal or isolated changes generally raise more questions and concerns
   than changes that seek to address a larger perspective.

Explanation
~~~~~~~~~~~

* Title convention: Use words indicating explanation in the title.
  Like **Understanding <subject>**, **Dive into <subject>**, **Introduction to <subject>** etc.
* Introduce the scope in the first paragraph: **“This article introduces ...”**.
  Write this as the very first thing,
  then re-read it and potentially shorten it later in your writing process.
* Cross-reference the related How-to Guide.
  Put a ``seealso::`` somewhere visible.
  It should likely be placed right after the introduction,
  and if the article is very short, maybe at the bottom.
* Consider adding an Examples section.
* Can you add screenshots or diagrams?

How-to guides
~~~~~~~~~~~~~

* Title should begin with **“How to ...”**.
  If the how-to guide is specific for a tool, make sure to note it in the title.
* Navigation titles should not contain the “How to” part.
  Navigation title for "How to create a thing" is **Creating a thing**.
* Introduce the scope: **“In this guide, we will…”**

  * Introduction paragraph suggestions:

    * "This guide shows <something>. <motivation>"
    * "<motivation>. This guide shows you how."

* Cross-reference related explanation.
  Put a ``seealso::`` somewhere visible,
  It should likely be placed right after the introduction
  and if the article is very short, maybe at the bottom.
* Try to avoid a “trivial” how-to,
  i.e. a step-by-step guide that just states what is on a page without further information.
  You can ask questions like:

  * Can this how-to contain recommendations and practical advice without breaking the how-to format?
  * Can this how-to be expanded with relevant troubleshooting?
  * Worst-case:
    Is this how-to describing a task that's so trivial and self-evident
    that we might as well remove it?

* Consider if an animation can be embedded:
  `Here is an article about 'gif-to-video' <https://www.smashingmagazine.com/2018/11/gif-to-video/#replace-animated-gifs-with-video-in-the-browser>`__

Reference
~~~~~~~~~

We have not started organizing the Reference section yet,
guidelines pending.

Tutorial
~~~~~~~~

.. note:: We don’t really have tutorials targeted in the systematic refactor, so this checklist isn’t very important right now.

* "Getting started with <subject>" is likely a good start!
* Cross-reference related explanation and how-to.
* Try not to explain things too much, and instead link to the explanation content.
* **Refactor other resources** so you can use references instead of disturbing the flow of the tutorial.
