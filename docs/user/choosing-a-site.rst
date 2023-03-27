.. This page seeks to put out lots of pointers to other articles in the documentation
.. while giving an introduction that can be read consecutively.

Choosing a dedicated documentation platform
===========================================

In this article,
we explain the major reasons behind having a platform dedicated to build and publish documentation projects.
In other words,
we dive into some of the reasons behind Read the Docs' existence and vision.

Let us start with the major benefits of choosing a dedicated documentation platform:

* Life-cycle: Handling challenges and complexities that documentation projects face
* Freedom to choose your documentation tools
* Workflow: Supportive of agile workflows and automating repetitive tasks

When observing a documentation project,
we might understand documentation as simply one or more deliverables of the project, such as:
A website, a PDF document, an API documentation.
We might simply focus on choosing the software tools generate a static website or a set of :doc:`documentation output formats </downloadable-documentation>`.

Choosing to use Read the Docs as a first-step,
allows you to focus on other critical choices,
such as documentation tools and documentation structure.

Supporting the life-cycle of a documentation project
----------------------------------------------------

It's common to think that documentation is as simple as maintaining some content for a static website. Job done.
Read the Docs is a platform that's based on decades of experience in operating documentation tools that have proven their value over the same span of time.
It handles challenges that you might face down the road by having the right features ready when you need them.

Example: Automated versioning and redirects
    Once a documentation project is bootstrapped,
    the software project might change its version and remove and add features.
    Old versions of the project still need to be able to refer to their original documentation while new versions should not be unnecessarily complicated by documenting old features.
    That is why Read the Docs supports versioning out-of-the-box and also gives you a mature set of options for creating automated redirects.
    It's not just simple A=>B redirects, but they can follow your own patterns or work only on specific versions.

Example: Analytics
    Documentation websites also benefit from knowing which pages are popular and how people discover them through online search.
    It would be understandable that this is not an immediate requirement for a documentation project,
    but the need eventually arises,
    and why should every documentation project have to implement their own analytics solution?

A very straight-forward way to understand Read the Docs is to look at our :doc:`feature reference </reference/features>`.
All these features ultimately sustain the life-cycle of a documentation project.

.. insert life-cycle diagram.

Freedom to choose documentation tools
-------------------------------------


Agile workflows with Continuous Integration and Deployment (CI/CD)
------------------------------------------------------------------


Types of documentation projects
-------------------------------


Software projects
~~~~~~~~~~~~~~~~~

...

Scientific writing and academic projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

...

Differences between Community and Business
------------------------------------------

While many of our features are available on both of these platforms, there
are some key differences between our two platforms.

.. seealso::

   `Our website: Comparison of Community and all subscription plans <https://about.readthedocs.org/pricing/>`__
      Refer to the complete table of features included in all of the Read the Docs solutions available.

|org_brand|
~~~~~~~~~~~

|org_brand| is exclusively for hosting open source documentation. We support
open source communities by providing free documentation building and hosting
services, for projects of all sizes.

Important points:

* Open source project hosting is always free
* All documentation sites include advertising
* Only supports public VCS repositories
* All documentation is publicly accessible to the world
* Less build time and fewer build resources (memory & CPU)
* Email support included only for issues with our platform
* Documentation is organized by projects

You can sign up for an account at https://readthedocs.org.

|com_brand|
~~~~~~~~~~~

|com_brand| is meant for companies and users who have more complex requirements
for their documentation project. This can include commercial projects with
private source code, projects that can only be viewed with authentication, and
even large scale projects that are publicly available.

Important points:

* Hosting plans require a paid subscription plan
* There is no advertising on documentation sites
* Allows importing private and public repositories from VCS
* Supports private versions that require authentication to view
* Supports team authentication, including SSO with Google, GitHub, GitLab, and Bitbucket
* More build time and more build resources (memory & CPU)
* Includes 24x5 email support, with 24x7 SLA support available
* Documentation is organized by organization, giving more control over permissions

You can sign up for an account at https://readthedocs.com.

Questions?
----------

If you have a question about which platform would be best,
email us at support@readthedocs.org.
