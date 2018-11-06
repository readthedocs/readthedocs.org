Designing Read the Docs
=======================

So you're thinking of contributing some of your
time and design skills to Read the Docs? That's
**awesome**. This document will lead you through
a few features available to ease the process of
working with Read the Doc's CSS and static assets.

To start, you should follow the :doc:`install` instructions
to get a working copy of the Read the Docs repository locally.

Style Catalog
-------------

Once you have RTD running locally, you can open ``http://localhost:8000/style-catalog/``
for a quick overview of the currently available styles.

.. image:: /img/headers.png

This way you can quickly get started writing HTML -- or if you're
modifying existing styles you can get a quick idea of how things
will change site-wide.

Readthedocs.org Changes
-----------------------

Styles for the primary RTD site are located in ``media/css`` directory.

These styles only affect the primary site -- **not** any of the generated
documentation using the default RTD style.

Sphinx Template Changes
-----------------------

Styles for generated documentation are located in ``readthedocs/templates/sphinx/_static/rtd.css``

Of note, projects will retain the version of that file they were last built with -- so if you're
editing that file and not seeing any changes to your local built documentation, you need to rebuild
your example project.

Contributing
------------

Contributions should follow the :doc:`contribute` guidelines where applicable -- ideally you'll
create a pull request against the `Read the Docs GitHub project`_ from your forked repo and include
a brief description of what you added / removed / changed, as well as an attached image (you can just
take a screenshot and drop it into the PR creation form) of the effects of your changes.

There's not a hard browser range, but your design changes should work reasonably well across all major
browsers, IE8+ -- that's not to say it needs to be pixel-perfect in older browsers! Just avoid
making changes that render older browsers utterly unusable (or provide a sane fallback).

Brand Guidelines
----------------

Find our branding guidelines in our guidelines documentation: https://read-the-docs-guidelines.readthedocs-hosted.com.

.. _Read the Docs GitHub project: https://github.com/rtfd/readthedocs.org/pulls

