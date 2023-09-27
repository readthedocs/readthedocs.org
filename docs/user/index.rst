Read the Docs: documentation simplified
=======================================

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: 🚀 Tutorials

   /tutorial/index
   /intro/getting-started-with-sphinx
   /intro/getting-started-with-mkdocs
   /intro/import-guide
   /config-file/index
   /examples

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: 💡 Explanation

   /choosing-a-site
   /integrations
   /downloadable-documentation
   /environment-variables
   /subprojects
   /localization
   /explanation/advanced
   /explanation/methodology

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: 🪄 How-to guides

   Project setup and configuration </guides/setup/index>
   Build process </guides/build/index>
   Upgrading and maintaining projects </guides/maintenance/index>
   Content, themes and SEO </guides/content/index>
   Security and access </guides/access/index>
   Account management </guides/management/index>
   Best practice </guides/best-practice/index>
   Troubleshooting problems </guides/troubleshooting/index>

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: 📚 Reference

   /reference/features
   /config-file/v2
   /builds
   /build-customization
   /server-side-search/syntax
   /faq
   /api/index
   /changelog
   /about/index
   Developer Documentation <https://dev.readthedocs.io>

.. meta::
   :description lang=en: Automate building, versioning, and hosting of your technical documentation continuously on Read the Docs.

.. Adds a hidden link for the purpose of validating Read the Docs' Mastodon profile
.. raw:: html

   <a style="display: none;" rel="me" href="https://fosstodon.org/@readthedocs">Mastodon</a>

Read the Docs simplifies software documentation
by building, versioning, and hosting of your docs, automatically.
Treating documentation like code keeps your team in the same tools,
and your documentation up to date.

|:arrows_counterclockwise:| Up to date documentation
    Whenever you push code to Git,
    Read the Docs will automatically build your docs
    so your code and documentation are always up-to-date.
    Get started with our :doc:`tutorial </tutorial/index>`.

|:card_index_dividers:| Documentation for every version
    Read the Docs can host multiple versions of your docs.
    Keep your 1.0 and 2.0 documentation online,
    pulled directly from Git.
    Start hosting all your :doc:`versions </versions>`.

|:heartbeat:| Open source and user focused
    Our company is bootstrapped and 100% user-focused,
    so our product gets better for our users instead of our investors.
    |org_brand| hosts documentation for over 100,000 large
    and small open source projects.
    |com_brand| supports hundreds of organizations with product and internal documentation.
    Learn more about :doc:`our two platforms </choosing-a-site>`.

First time here?
----------------

We have a few places for you to get started:

.. descriptions here are active

🚀 :doc:`/tutorial/index`
  Take the first practical steps with Read the Docs.

🚀 :doc:`/examples`
  Start your journey with an example project to hit the ground running.

🚀 :doc:`All tutorials </tutorials/index>`
  Using documentation tools like Sphinx or MkDocs for the first time or importing an existing project?
  We have the tutorials to get you started!

.. TODO: This above item needs its article to be finished in a separate PR
.. because of what seems to be a bug in Sphinx, we get two <dl> items
.. if we put comments between items.
.. https://github.com/readthedocs/readthedocs.org/pull/10071
.. This page isn't ready for front page treatment
.. doc:`Why use a dedicated documentation platform? </integrations>`
.. An introduction to some of the most important reasons for using a *Documentation CI* and build *docs as code*.


Explanation
-----------

Get a high-level overview of our platform:

.. Descriptions here are focused on learning

.. TODO: This next item needs its article to be finished in a separate PR
.. https://github.com/readthedocs/readthedocs.org/pull/10071

💡 :doc:`Continuous Documentation </integrations>`
  Discover the advantages of having your documentation continuously deployed.

💡 :doc:`/choosing-a-site`
  Learn about the differences between |org_brand| and |com_brand|.

💡 :doc:`/explanation/advanced`
  Get familiar with some of the more advanced topics of building and deploying documentation with Read the Docs.

💡 :doc:`All explanation articles </explanation/index>`
  Browse all our explanation articles.


How-to guides
-------------

Need to get something specific done?
These guides provide step-by-step instructions in key areas to get you up to speed faster:

.. Descriptions here are active, learn, setup, etc.
.. The chosen sample of how-tos is intended reflect to width of the how-to section
.. i.e. NOT only what is most popular or easiest for beginners.

🪄 :doc:`/guides/pull-requests`
  Setup pull request builds and enjoy previews of each commit.

🪄 :doc:`/analytics`
  Learn more about how users are interacting with your documentation.

🪄 :doc:`/guides/cross-referencing-with-sphinx`
  Learn how to use cross-references in a Sphinx project.

🪄 :doc:`All how-to guides </guides/index>`
  Browser the entire catalog for many more how-to guides.

Reference
---------

Need to know how something works?
Here are a few of the most important reference docs:

.. Descriptions here sound like reference

📚 :doc:`/reference/features`
  Overview of all the main features of Read the Docs.

📚 :doc:`/config-file/v2`
  Information for our configuration file: ``.readthedocs.yaml``.

📚 :doc:`/builds`
  Overview of how documentation builds happen.

📚 :doc:`/build-customization`
  Information on how to add your own build logic or replace default build steps.

📚 :doc:`/api/index`
  Automate your documentation with our API and save yourself some work.
