Enabling Build Notifications
============================

Using email
-----------

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Going to **Admin > Notifications** in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

You should now get notified on your email when your builds fail!

Using webhook
-------------

Read the Docs also allows webhooks configuration to receive notification regarding builds fails.

Take these steps to enable build notifications using webhook:

* Going to **Admin > Notifications** in your project.
* Fill in the **Url** field under the **New Webhook Notifications** heading
* Submit the form

The project name, slug and its bulid instance that failed will be sent as POST request to your webhook url:

.. code-block:: json
       
       {       
            "name": "Read the Docs",
            "slug": "rtd",
            "build": {
                "id": 6321373,
                "success": false,
                "date": "2017-02-15 20:35:54",
            }
       }

You should now get notified on your webhook when your builds fail!
