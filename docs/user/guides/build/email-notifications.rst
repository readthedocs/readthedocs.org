How to setup email notifications
================================

In this guide,
you can learn how to setup a simple build notification via email.

Read the Docs allows you to configure emails that will be notified on failing builds.
This makes sure that you are aware of failures happening in an otherwise automated process.

.. seealso::

    :doc:`/guides/build/webhooks`
        How to use webhooks to be notified about builds on popular platforms like Slack and Discord.

    :doc:`/pull-requests`
        Similarly to email notifications,
        you can also configure automated feedback for your pull requests.


Email notifications
-------------------

Take these steps to enable build notifications using email:

* Go to :menuselection:`Admin --> Notifications` in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Press :guilabel:`Add` and the email is saved and will be displayed in the list of **Existing notifications**.

A newly added email will be notified once a build fails.


.. note::

   We don't send email notifications on :doc:`builds from pull requests </pull-requests>`.
