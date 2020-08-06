Getting Started with Sphinx
===========================

.. meta::
   :description lang=en: Get started writing technical documentation with Sphinx and publishing to Read the Docs.


Sphinx is a powerful documentation generator that
has many great features for writing technical documentation including:

* Generate web pages, printable PDFs, documents for e-readers (ePub),
  and more all from the same sources
* You can use reStructuredText or :ref:`Markdown <intro/getting-started-with-sphinx:Using Markdown with Sphinx>`
  to write documentation
* An extensive system of cross-referencing code and documentation
* Syntax highlighted code samples
* A vibrant ecosystem of first and third-party :doc:`extensions <sphinx:usage/extensions/index>`

Quick start video
-----------------

This screencast will help you get started or you can
:ref:`read our guide below <intro/getting-started-with-sphinx:Quick start>`.

.. raw:: html

    <div style="text-align: center; margin-bottom: 2em;">
    <iframe width="100%" height="350" src="https://www.youtube-nocookie.com/embed/oJsUvBQyHBs?rel=0" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
    </div>


Quick start
-----------

Assuming you have Python already, :doc:`install Sphinx <sphinx:usage/installation>`:

.. prompt:: bash $

    pip install sphinx

Create a directory inside your project to hold your docs:

.. prompt:: bash $

    cd /path/to/project
    mkdir docs

Run ``sphinx-quickstart`` in there:

.. prompt:: bash $

    cd docs
    sphinx-quickstart

This quick start will walk you through creating the basic configuration; in most cases, you
can just accept the defaults. When it's done, you'll have an ``index.rst``, a
``conf.py`` and some other files. Add these to revision control.

Now, edit your ``index.rst`` and add some information about your project.
Include as much detail as you like (refer to the :doc:`reStructuredText syntax <sphinx:usage/restructuredtext/basics>`
or `this template`_ if you need help). Build them to see how they look:

.. prompt:: bash $

    make html

Your ``index.rst`` has been built into ``index.html``
in your documentation output directory (typically ``_build/html/index.html``).
Open this file in your web browser to see your docs.

.. figure:: /_static/images/first-steps/sphinx-hello-world.png
   :figwidth: 500px
   :target: /_static/images/first-steps/sphinx-hello-world.png
   :align: center

   Your Sphinx project is built

Edit your files and rebuild until you like what you see, then commit your changes and push to your public repository.
Once you have Sphinx documentation in a public repository, you can start using Read the Docs
by :doc:`importing your docs </intro/import-guide>`.

.. warning::

   We strongly recommend to :ref:`pin the Sphinx version <guides/specifying-dependencies:Specifying Dependencies>`
   used for your project to build the docs to avoid potential future incompatibilities.

.. _this template: https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/#id1

Using Markdown with Sphinx
--------------------------

You can use Markdown and reStructuredText in the same Sphinx project.
We support this natively on Read the Docs, and you can do it locally:

.. prompt:: bash $

    pip install recommonmark

Then in your ``conf.py``:

.. code-block:: python

   extensions = ['recommonmark']

.. warning:: Markdown doesn't support a lot of the features of Sphinx,
          like inline markup and directives. However, it works for
          basic prose content. reStructuredText is the preferred
          format for technical documentation, please read `this blog post`_
          for motivation.

.. _this blog post: https://www.ericholscher.com/blog/2016/mar/15/dont-use-markdown-for-technical-docs/


External resources
------------------

Here are some external resources to help you learn more about Sphinx.

* `Sphinx documentation`_
* :doc:`RestructuredText primer <sphinx:usage/restructuredtext/basics>`
* `An introduction to Sphinx and Read the Docs for technical writers`_

.. _Sphinx documentation: https://www.sphinx-doc.org/
.. _An introduction to Sphinx and Read the Docs for technical writers: https://www.ericholscher.com/blog/2016/jul/1/sphinx-and-rtd-for-writers/
