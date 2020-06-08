Read the Docs: Documentation Simplified
=======================================

.. meta::
   :description lang=en: Automate building, versioning, and hosting of your technical documentation continuously on Read the Docs.

`Read the Docs`_ simplifies software documentation
by building, versioning, and hosting of your docs, automatically.
Think of it as *Continuous Documentation*.

Never out of sync |:arrows_counterclockwise:|
    Whenever you push code to your favorite version control system,
    whether that is Git, Mercurial, Bazaar, or Subversion,
    Read the Docs will automatically build your docs
    so your code and documentation are always up-to-date.
    Read more about :doc:`/webhooks`.

Multiple versions |:card_index_dividers:|
    Read the Docs can host and build multiple versions of your docs
    so having a 1.0 version of your docs and a 2.0 version
    of your docs is as easy as having a separate branch or tag in your version control system.
    Read more about :doc:`/versions`.

Open Source and User Focused |:heartbeat:|
    Our code is free and `open source <https://github.com/readthedocs/>`_.
    :doc:`Our company </about>` is bootstrapped and 100% user focused.
    |org_brand| hosts documentation for over 100,000 large 
    and small open source projects,
    in almost every human and computer language.
    |com_brand| supports hundreds of organizations with product and internal documentation.

.. _Read the docs: https://readthedocs.org/

You can find out more about our all the :doc:`/features` in these pages.

First steps
-----------

Are you new to software documentation
or are you looking to use your existing docs with Read the Docs?
Learn about documentation authoring tools such as Sphinx and MkDocs
to help you create fantastic documentation for your project.

* **Getting started**:
  :doc:`With Sphinx </intro/getting-started-with-sphinx>` |
  :doc:`With MkDocs </intro/getting-started-with-mkdocs>` |
  :doc:`Feature Overview </features>` |
  :doc:`/choosing-a-site`

* **Importing your existing documentation**:
  :doc:`Import guide </intro/import-guide>`


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: First steps

   /intro/getting-started-with-sphinx
   /intro/getting-started-with-mkdocs

   /intro/import-guide
   /features
   /choosing-a-site


Getting started with Read the Docs
-----------------------------------

Learn more about configuring your automated documentation builds
and some of the core features of Read the Docs.

* **Overview of core features**:
  :doc:`Incoming webhooks </webhooks>` |
  :doc:`/custom_domains` |
  :doc:`/versions` |
  :doc:`/downloadable-documentation` |
  :doc:`/hosting` |
  :doc:`/server-side-search`

* **Connecting with GitHub, BitBucket, or GitLab**:
  :doc:`Connecting your VCS account </connected-accounts>` | 
  :doc:`VCS webhooks </webhooks>`

* **Read the Docs build process**:
  :doc:`Configuration reference </config-file/index>` |
  :doc:`Build process </builds>` |
  :doc:`/badges` |

* **Troubleshooting**:
  :doc:`/support` |
  :doc:`Frequently asked questions </faq>`

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Getting started

   /config-file/index
   /webhooks
   /custom_domains
   /versions
   /downloadable-documentation
   /server-side-search
   /hosting

   /connected-accounts

   /builds
   /badges

   /support
   /faq


Step-by-step Guides
-------------------

These guides will help walk you through specific use cases
related to Read the Docs itself, documentation tools like Sphinx and MkDocs
and how to write successful documentation.

* :doc:`/guides/tools`
* :doc:`/guides/platform`
* :doc:`/guides/commercial`

.. toctree::
 :maxdepth: 2
 :hidden:
 :caption: Step-by-step Guides

 /guides/tools
 /guides/platform
 /guides/commercial

Advanced features of Read the Docs
----------------------------------

Read the Docs offers many advanced features and options.
Learn more about these integrations and how you can get the most
out of your documentation and Read the Docs.

* **Advanced project configuration**:
  :doc:`subprojects` |
  :doc:`Single version docs <single_version>`

* **Multi-language documentation**:
  :doc:`Translations and localization <localization>`

.. TODO: Move user-defined to Getting started, they are core functionality

* **Redirects**:
  :doc:`User defined redirects <user-defined-redirects>` |
  :doc:`Automatic redirects <automatic-redirects>`

* **Versions**
  :doc:`Automation rules <automation-rules>`

* **Topic specific guides**:
  :doc:`How-to guides <guides/index>`

* **Extending Read the Docs**:
  :doc:`REST API <api/index>`

.. toctree::
   :maxdepth: 2
   :hidden:
   :glob:
   :caption: Advanced features

   subprojects
   single_version

   localization

   user-defined-redirects
   automatic-redirects

   automation-rules


   api/index


The Read the Docs project and organization
------------------------------------------

Learn about Read the Docs, the project and the company,
and find out how you can get involved and contribute to the development and success
of Read the Docs and the larger software documentation ecosystem.

* **Getting involved with Read the Docs**:
  :doc:`Contributing <contribute>` |
  :doc:`Development setup </development/standards>` |
  :doc:`roadmap` |
  :doc:`Code of conduct <code-of-conduct>`

* **Policies & Process**:
  :doc:`security` |
  :doc:`Privacy policy <privacy-policy>` |
  :doc:`Terms of service <terms-of-service>` |
  :doc:`DMCA takedown policy <dmca/index>` |
  :doc:`Policy for abandoned projects <abandoned-projects>` |
  :doc:`Release notes & changelog <changelog>`

* **The people and philosophy behind Read the Docs**:
  :doc:`About Us </about>` |
  :doc:`Team <team>` |
  :doc:`Open source philosophy <open-source-philosophy>` |
  :doc:`Our story <story>`

* **Financial and material support**:
  :doc:`advertising/index` |
  :doc:`Sponsors <sponsors>`

* **Read the Docs for Business**:
  :doc:`Support and additional features <commercial/index>`

* **Running your own version of Read the Docs**:
  :doc:`Private installations <custom_installs/index>`


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: About Read the Docs

   contribute
   development/index
   roadmap
   gsoc
   code-of-conduct

   security
   privacy-policy
   terms-of-service
   dmca/index
   abandoned-projects
   changelog

   about
   team
   open-source-philosophy
   story

   advertising/index
   sponsors

   commercial/index

   custom_installs/index
