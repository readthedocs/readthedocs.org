Google Summer of Code
=====================

.. note:: Thanks for your interest in Read the Docs!
          Please follow the instructions in `Getting Started`_,
          as a good place to start.
          **Contacting us will not increase your chance of being accepted,
          but opening Pull Requests with docs and tests will.**

Read the Docs is excited to be in the Google Summer of Code in 2019.
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

Getting Started
---------------

The :doc:`/install` doc is probably the best place to get going.
It will walk you through getting a basic environment for Read the Docs setup. 

Then you can look through our :doc:`/contribute` doc for information on how to get started contributing to RTD.

People who have a history of submitting pull requests will be prioritized in our Summer of Code selection process.

Want to get involved?
---------------------

If you're interested in participating in GSoC as a student, you can apply during the normal process provided by Google. We are currently overwhelmed with interest, so we are not able to respond individually to each person who is interested.

Mentors
-------

Currently we have a few folks signed up:

* Eric Holscher
* Manuel Kaufmann
* Anthony Johnson
* Safwan Rahman

.. warning:: Please do not reach out directly to anyone about the Summer of Code.
             It will **not** increase your chances of being accepted!

Project Ideas
-------------

We have written our some loose ideas for projects to work on here.
We are also open to any other ideas that students might have. 

**These projects are sorted by priority.**
We will consider the priority on our roadmap as a factor,
along with the skill of the student,
in our selection process.

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

Autobuild docs for Pull Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It would be great to automatically build docs for Pull Requests in GitHub repos that our users have.
Currently we don't support this,
and it's one of our most requested features.

This would include:

* Modeling Pull Requests as a type of version alongside Tags and Branches
* Modifying how we upload HTML docs to store them in a place like S3 for long term storage
* Build integration with GitHub to send the status notifications when a PR is building and complete

More info here: 

* https://github.com/rtfd/readthedocs.org/issues/1340
* https://github.com/rtfd/readthedocs.org/issues/2465


Build a new Sphinx theme
~~~~~~~~~~~~~~~~~~~~~~~~

Sphinx v2 will introduce a new format for themes,
supporting HTML5 and new markup.
We are hoping to buid a new Sphinx theme that supports this new structure.

This project would include:

* A large amount of design, including working with CSS & SASS
* Iterating with the community to build something that works well for a number of use cases

This is not as well defined as the other tasks,
so would require a higher level of skill from an incoming student.

Better MkDocs integration
~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we don't have a good integration with MkDocs as we do with Sphinx.
And it's hard to maintain compatibility with new versions.

This project would include:

* Support the latest version of MkDocs
* Support downloads (`#1939`_)
* Write a plugin to allow us to have more control over the build process (`#4924`_)
* Support search (`#1088`_)

.. _#1939: https://github.com/rtfd/readthedocs.org/issues/1939
.. _#4924: https://github.com/rtfd/readthedocs.org/issues/4924
.. _#1088: https://github.com/rtfd/readthedocs.org/issues/1088

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

Improve Translation Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we have our documentation & website translated on Transifex,
but we don't have a management process for it.
This means that translations will often sit for months before making it back into the site and being available to users.

This project would include putting together a workflow for translations:

* Communicate with existing translators and see what needs they have
* Help formalize the process that we have around Transifex to make it easier to contribute to
* Improve our tooling so that integrating new translations is easier

Support for additional build steps for linting and testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Additional Ideas
~~~~~~~~~~~~~~~~

We have some medium sized projects sketched out in our issue tracker with the tag *Feature*.
Looking through `these issues`_ is a good place to start.
You might also look through our `milestones`_ on GitHub,
which provide outlines on the larger tasks that we're hoping to accomplish.

.. _these issues: https://github.com/rtfd/readthedocs.org/issues?direction=desc&labels=Feature&page=1&sort=updated&state=open
.. _milestones: https://github.com/rtfd/readthedocs.org/milestones

Thanks
------

This page was heavily inspired by Mailman's similar `GSOC page`_.
Thanks for the inspiration.

.. _GSOC page: http://wiki.list.org/display/DEV/Google+Summer+of+Code+2014
