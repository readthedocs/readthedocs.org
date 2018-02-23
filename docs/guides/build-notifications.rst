Enabling Build Notifications
============================

Using Email
******************

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Going to **Admin > Notifications** in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

You should now get notified on your email when your builds fail!

Using Webhook
******************

Read the Docs also allows webhooks configuration to receive notification regarding builds fails.

Take these steps to enable build notifications using webhook:

* Going to **Admin > Notifications** in your project.
* Fill in the **Url** field under the **New Webhook Notifications** heading
* Submit the form

The project name, id and its bulid instance that failed will be sent to your webhook url:

.. code-block:: json
       
       {       
            'name': project.name,
            'slug': project.slug,
            'build': {
                'id': build.id,
                'success': build.success,
                'date': build.date.strftime('%Y-%m-%d %H:%M:%S'),
            }
       }




You should now get notified on your webhook when your builds fail!
