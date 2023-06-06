How to enable email notifications
=================================

In this guide, you can learn how to setup build notification via email.

.. note::

   Currently we don't send email notifications on :doc:`builds from pull requests </pull-requests>`.

.. tip::
    :doc:`/pull-requests`
        Similarly to email notifications,
        you can also configure automated feedback for your pull requests.


Email notifications
-------------------

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Go to :menuselection:`Admin --> Notifications` in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

Who is notified?
----------------

If you are a single owner of a project,
*you* will get notified.

If your project has several members,
then the following are notified:

* All :term:`maintainers <maintainer>` (|org_brand|)
* All owners of an :doc:`organization </commercial/organizations>` (|com_brand|)
  that owns the project,
  or members of teams with admin access to the project.
