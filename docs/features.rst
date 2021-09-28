Read the Docs features
======================

Read the Docs offers a number of platform features that are possible because we both build and host documentation for you.


Automatic Documentation Deployment
----------------------------------

We integrate with GitHub, BitBucket, and GitLab.
We automatically create webhooks in your repository,
which tell us whenever you push a commit.
We will then build and deploy your docs every time you push a commit.
This enables a workflow that we call *Continuous Documentation*:

**Once you set up your Read the Docs project,
your users will always have up-to-date documentation.**

Learn more about :doc:`/webhooks`.

Custom Domains & White Labeling
-------------------------------

When you import a project to Read the Docs,
we assign you a URL based on your project name.
You are welcome to use this URL,
but we also fully support custom domains for all our documentation projects.

Learn more about :doc:`/custom_domains`.

Versioned Documentation
-----------------------

We support multiple versions of your documentation,
so that users can find the exact docs for the version they are using.
We build this on top of the version control system that you're already using.
Each version on Read the Docs is just a tag or branch in your repository.

You don't need to change how you version your code,
we work with whatever process you are already using.
If you don't have a process,
we can recommend one.

Learn more about :doc:`/versions`.

Downloadable Documentation
--------------------------

Read the Docs supports building multiple formats for Sphinx-based projects:

* PDF
* ePub
* Zipped HTML

This means that every commit that you push will automatically update your PDFs as well as your HTML.

This feature is great for users who are about to get on a plane and want offline docs,
as well as being able to ship your entire set of documentation as one file.

Learn more about :doc:`/downloadable-documentation`.

Full-Text Search
----------------

We provide search across all the projects that we host.
This actually comes in two different search experiences:
dashboard search on the Read the Docs dashboard and in-doc search on documentation sites, using your own theme and our search results.

We offer a number of search features:

* Search across :doc:`subprojects </subprojects>`
* Search results land on the exact content you were looking for
* Search across projects you have access to (available on |com_brand|)
* A full range of :doc:`search operators </guides/advanced-search>` including exact matching and excluding phrases.

Learn more about :doc:`/server-side-search`.

Open Source and Customer Focused
--------------------------------

Read the Docs cares deeply about our customers and our community.
As part of that commitment,
all of the source code for Read the Docs is open source.
This means there's no vendor lock-in,
and you are welcome to :doc:`contribute </contribute>` the features you want or run your own instance.

Our bootstrapped company is owned and controlled by the founders,
and fully funded by our customers and advertisers.
That allows us to focus 100% of our attention on building the best possible product for you.

Learn more :doc:`/about`.
