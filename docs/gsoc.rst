Google Summer of Code
=====================

Read the Docs is hoping to participate in the Google Summer of Code in 2018.
This page will contain all the information for students and anyone else interested in helping.

Required Skills
---------------

Incoming students will need the following skills:

* Intermediate python programming
* Familiarity with Markdown, reStructuredText, or some other plain text markup language
* Familiarity with git, or some other source control
* Ability to set up your own development environment for Read the Docs
* An interest in documentation and improving open source documentation tools would be great too!

We're happy to help you get up to speed,
but the more you are able to demonstrate ability in advance,
the more likely we are to choose your application! 

Getting Started
---------------

The :doc:`/install` doc is probably the best place to get going.
It will walk you through getting a basic environment for Read the Docs setup. 

Then you can look through our :doc:`contribute` doc for information on how to get started contributing to RTD.

People who has a history of submitting issues and pull requests will be prioritized in our Summer of Code selection process,
so don't be shy!

Want to get involved?
---------------------

If you're interested in participating in GSoC as a student, you can also post an `issue <https://github.com/rtfd/readthedocs.org/issues>`_ on GitHub to let us know. We will be happy to help direct you or answer any questions you may have there.

Project Ideas
-------------

We have written our some loose ideas for projects to work on here.
We are also open to any other ideas that students might have. 

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

Support for additional build steps for linting, testing, and other useful things
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently we only build documentation on Read the Docs,
but we'd also like to add additional build steps that lets users perform more actions.
This would likely take the form of wraping some of the existing `Sphinx builders <http://www.sphinx-doc.org/en/stable/builders.html>`_,
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

We have some medium sized projects sketched out in our issue tracker with the tag *Feature Overview*.
Looking through `these issues`_ is a good place to start.
You can also look through any additional open issue to get ideas or what to work on.

.. _these issues: https://github.com/rtfd/readthedocs.org/issues?direction=desc&labels=Feature+Overview&page=1&sort=updated&state=open

Possible Mentors
----------------

Anyone listed in Development Team on our :doc:`/team` page would be a great person to chat with about mentoring!

Thanks
------

This page was heavily inspired by Mailman's similar `GSOC page`_.
Thanks for the inspiration.

.. _GSOC page: http://wiki.list.org/display/DEV/Google+Summer+of+Code+2014