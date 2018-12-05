Google Summer of Code
=====================

.. note:: Thanks for your interest in Read the Docs!
          We are working hard to update the ideas list now that we are accepted in GSOC.
          Please give us a little while to work on things,
          and check back on this page for updates.

Read the Docs is participating in the Google Summer of Code in 2018.
This page will contain all the information for students and anyone else interested in helping.

Skills
------

Incoming students will need the following skills:

* Intermediate Python & Django programming
* Familiarity with Markdown, reStructuredText, or some other plain text markup language
* Familiarity with git, or some other source control
* Ability to set up your own development environment for Read the Docs
* Basic understanding of web technologies (HTML/CSS/JS)
* An interest in documentation and improving open source documentation tools!

We're happy to help you get up to speed,
but the more you are able to demonstrate ability in advance,
the more likely we are to choose your application! 

Mentors
-------

Currently we have a few folks signed up:

* Eric Holscher
* Manuel Kaufmann
* Anthony Johnson

.. warning:: Please do not reach out directly to anyone about the Summer of Code.
             It will **not** increase your chances of being accepted!

Getting Started
---------------

The :doc:`/install` doc is probably the best place to get going.
It will walk you through getting a basic environment for Read the Docs setup. 

Then you can look through our :doc:`/contribute` doc for information on how to get started contributing to RTD.

People who have a history of submitting pull requests will be prioritized in our Summer of Code selection process.

Want to get involved?
---------------------

If you're interested in participating in GSoC as a student, you can apply during the normal process provided by Google. We are currently overwhelmed with interest, so we are not able to respond individually to each person who is interested.

Project Ideas
-------------

We have written our some loose ideas for projects to work on here.
We are also open to any other ideas that students might have. 

**These projects are sorted by priority.**
We will consider the priority on our roadmap as a factor,
along with the skill of the student,
in our selection process.

Refactor & improve our search code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we're using a homegrown library for Elastic Search.
There is a new `elasticsearch-dsl <http://elasticsearch-dsl.readthedocs.io/en/latest/>`_ library that we should be using.
This project will include:

* Improving our search indexing
* Refactoring how we "model" our search data to use elasticsearch-dsl Models
* Add additional search data into our indexes, like the programming languages, type of document (tutorial, api, etc.) and other data for users to filter by
* (Optional) Improve the UX of the search for users in various ways

Finish YAML config
~~~~~~~~~~~~~~~~~~

Currently we have a basic :doc:`/yaml-config` for Read the Docs.
It's still considered beta,
and there are a number of features that it doesn't support.
We need to support everying users can currently do from our website dashboard inside the YAML file,
and then plan a smooth transition path from the database UI to the YAML file.

This is a *large* project and will likely require a good deal of understanding of both Python as well as web technologies.
We have a `starting list of issues <https://github.com/rtfd/readthedocs.org/milestone/28>`_ put together,
but there will be much more work.

API V3
~~~~~~

We currently have a "v2" API that isn't well documented and doesn't allow users to write to it.
We want to continue using Django REST Framework for this,
but rethink how we're presenting our information to our users.

Currently we're showing everything as simple "models",
and we want to start exposing "methods" on our data,
similar to GitHub.

This is a large project and should only be done by someone who has done some basic API design previously. 

Improve Translation Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we have our documentation & website translated on Transifex,
but we don't have a management process for it.
This means that translations will often sit for months before making it back into the site and being available to users.

This project would include putting together a workflow for translations:

* Communicate with existing translators and see what needs they have
* Help formalize the process that we have around Transifex to make it easier to contribute to
* Improve our tooling so that integrating new translations is easier

Support for additional build steps for linting & testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we only build documentation on Read the Docs,
but we'd also like to add additional build steps that lets users perform more actions.
This would likely take the form of wrapping some of the existing `Sphinx builders <http://www.sphinx-doc.org/en/stable/builders.html>`_,
and giving folks a nice way to use them inside Read the Docs.

It would be great to have wrappers for the following as a start:

* Link Check (http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.linkcheck.CheckExternalLinksBuilder)
* Spell Check (https://pypi.python.org/pypi/sphinxcontrib-spelling/)
* Doctest (http://www.sphinx-doc.org/en/stable/ext/doctest.html#module-sphinx.ext.doctest)
* Coverage (http://www.sphinx-doc.org/en/stable/ext/coverage.html#module-sphinx.ext.coverage)

The goal would also be to make it quite easy for users to contribute third party build steps for Read the Docs,
so that other useful parts of the Sphinx ecosystem could be tightly integrated with Read the Docs.

Collections of Projects
~~~~~~~~~~~~~~~~~~~~~~~

This project involves building a user interface for groups of projects in Read the Docs (`Collections`).
Users would be allowed to create, publish, and search a `Collection` of projects that they care about.
We would also allow for automatic creation of `Collections` based on a project's ``setup.py`` or ``requirements.txt``.

Once a user has a `Collection`,
we would allow them to do a few sets of actions on them:

* Search across all the projects in the `Collection` with one search dialog
* Download all the project's documentation (PDF, HTMLZip, Epub) for offline viewing
* Build a landing page for the collection that lists out all the projects, and could even have a user-editable description, similar to our project listing page.

There is likely other ideas that could be done with `Collections` over time.

Integrated Redirects
~~~~~~~~~~~~~~~~~~~~

Right now it's hard for users to rename files.
We support redirects,
but don't create them automatically on file rename,
and our redirect code is brittle.

We should rebuild how we handle redirects across a number of cases:

* Detecting a file change in git/hg/svn and automatically creating a redirect
* Support redirecting an entire domain to another place
* Support redirecting versions

There will also be a good number of things that spawn from this, including version aliases and other related concepts, if this task doesn't take the whole summer.


Additional Ideas
~~~~~~~~~~~~~~~~

We have some medium sized projects sketched out in our issue tracker with the tag *Feature Overview*.
Looking through `these issues`_ is a good place to start.
You might also look through our `milestones`_ on GitHub,
which provide outlines on the larger tasks that we're hoping to accomplish.

.. _these issues: https://github.com/rtfd/readthedocs.org/issues?direction=desc&labels=Feature+Overview&page=1&sort=updated&state=open
.. _milestones: https://github.com/rtfd/readthedocs.org/milestones

Thanks
------

This page was heavily inspired by Mailman's similar `GSOC page`_.
Thanks for the inspiration.

.. _GSOC page: http://wiki.list.org/display/DEV/Google+Summer+of+Code+2014
