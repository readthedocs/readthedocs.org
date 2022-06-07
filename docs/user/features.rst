Read the Docs features
======================

.. TODO:

   We are linking to feature pages that are not already reviewed/reworked and some of them are not great.
   That's some work we could add to the follow sprints to make the main page and its links consistent.
   However, that amount of work is not trivial :)


.. TODO: Missing features in this page

   - Build customization
   - CDN
   - Business:
     - SSO
     - Auth Auditing

Read the Docs offers a number of platform features that are possible because we both build and host documentation for you.
This page shows some highlights for the main ones and points to external pages to learn more about them.


Continuous documentation
------------------------

.. TODO: rework this paragraph

We integrate with GitHub, BitBucket, and GitLab.
We automatically create webhooks in your repository,
which tell us whenever you push a commit.
We will then build and deploy your docs every time you push a commit.
This enables a workflow that we call *Continuous Documentation*:
once you set up your Read the Docs project,
your users will always have up-to-date documentation.

Learn more about :doc:`/integrations`.


Pull requests previews
----------------------

.. TODO:


Custom domains with SSL support
-------------------------------

:ref:`We assign your project a URL based on its name </hosting:subdomain-support>` so you can immediately start hosting your documentation.
However, if you prefer to use a domain that you already own, :doc:`you can configure Read the Docs to serve the documentation under your custom domain </custom-domains>`.


Versioned documentation
-----------------------

Read the Docs can serve :doc:`multiple versions of your project's documentation </versions>`.
This allows you to serve, for example, ``v1.0``, ``v2.0`` and ``v3.0`` together with some alias that we create automatically: ``latest`` and ``stable``.
In this example, ``latest`` will point to the default branch of your repository and ``stable`` will point to ``v3.0``.
With this setup, your users will find the exact documentation for the version of your project they are using.


Downloadable documentation
--------------------------

Read the Docs supports building :doc:`downloadable formats </downloadable-documentation>` like PDF, ePub and Zipped HTML for Sphinx-based projects.
All these formats will be kept in sync with the HTML version since they are built at the same time.


Full-Text search
----------------

We provide a :doc:`powerful search engine </server-side-search>` that understands projects' documentations.
It's able to differentiate a Python function's name from a module's name from the same function's name used on a narrative paragraph,
giving readers such a power that will help them always to find what they are looking for.


Open Source and customer focused
--------------------------------

Read the Docs cares deeply about our customers and our community.
As part of that commitment,
all of the source code for :doc:`Read the Docs is open source </about>`.
This means there's no vendor lock-in,
and you are welcome to :doc:`contribute <rtd-dev:contribute>` the features you want or run your own instance.

Our bootstrapped company is owned and controlled by the founders,
and fully funded by our customers and advertisers.
That allows us to focus 100% of our attention on building the best possible product for you.
