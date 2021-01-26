Enabling Build Notifications
============================

.. note::

   Currently we don't send notifications when
   a :doc:`build from a pull request fails </pull-requests>`.

Using email
-----------

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Go to :guilabel:`Admin` > :guilabel:`Notifications` in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

You should now get notified by email when your builds fail!

Using webhook
-------------

Read the Docs can also send webhooks when builds are triggered, successful or failed.

Take these steps to enable build notifications using a webhook:

* Go to :guilabel:`Admin` > :guilabel:`Notifications` in your project.
* Fill in the **URL** field under the **New Webhook Notifications** heading
* Submit the form

The project name, slug and its details for the build will be sent as POST request to your webhook URL:

.. code-block:: json

       {
            "name": "Read the Docs",
            "slug": "rtd",
            "build": {
                "id": 6321373,
                "commit": "e8dd17a3f1627dd206d721e4be08ae6766fda40",
                "state": "finished",
                "success": false,
                "date": "2017-02-15 20:35:54"
            }
       }

You should now get notified on your webhook when your builds start and finish (failure/success)!
