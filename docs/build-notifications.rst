Build Notifications and Webhooks
================================

.. note::

   Currently we don't send notifications nor trigger webhooks when
   a :doc:`build from a pull request fails </pull-requests>`.

Email notifications
-------------------

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Go to :guilabel:`Admin` > :guilabel:`Notifications` in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

You should now get notified by email when your builds fail!

Webhooks
--------

Read the Docs can also send webhooks when builds are triggered, successful or failed.

Take these steps to enable build notifications using a webhook:

* Go to :guilabel:`Admin` > :guilabel:`Webhooks` in your project.
* Fill in the **URL** field and select what events will trigger the webhook
* Modify the payload or leave the default (see below)
* Click on :guilabel:`Save`

.. figure:: /_static/images/webhooks-events.png
   :width: 80%
   :align: center
   :alt: URL and events for a webhook

   URL and events for a webhook

Every time one of the checked events triggers,
Read the Docs will send a POST request to your webhook URL.
The default payload will look like this:

.. code-block:: json

   {
       "event": "build:triggered",
       "name": "Read the Docs",
       "slug": "rtd",
       "version": "latest",
       "commit": "e8dd17a3f1627dd206d721e4be08ae6766fda40",
       "build": 6321373
   }

When a webhook is sent, a new entry will be added to the
"Recent Activity" table. By clicking on each individual entry,
you will see the server response, the webhook request, and the payload.

.. figure:: /_static/images/webhooks-activity.png
   :width: 80%
   :align: center
   :alt: Activity of a webhook

   Activity of a webhook

Custom payloads
~~~~~~~~~~~~~~~

You can customize the payload of the webhook to suit your needs,
as long as it is valid JSON. These are the available variable substitutions:

``${event}``
  Event that triggered the webhook, one of ``build:triggered``, ``build:failed``, or ``build:passed``.

``${build.id}``
  Build ID.

``${build.commit}``
  Commit corresponding to the build, if present (otherwise ``""``).

``${build.url}``
  URL of the build.

``${build.docsurl}``
  URL of the documentation corresponding to the build.

``${organization.name}``
  Organization name (Commercial only).

``${organization.slug}``
  Organization slug (Commercial only).

``${project.slug}``
  Project slug.

``${project.name}``
  Project name.

``${project.url}``
  URL of the project :term:`dashboard`.

``${version.slug}``
  Version slug.

``${version.name}``
  Version name.

Legacy webhooks
~~~~~~~~~~~~~~~

Webhooks created before the custom payloads functionality was added to Read the Docs
send a payload with the following structure:

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

To migrate to the new webhooks and keep the same structure,
you can use this payload:

.. code-block:: json

   {
       "name": "${project.name}",
       "slug": "${project.slug}",
       "build": {
           "id": "${build.id}",
           "commit": "${build.commit}",
           "state": "${build.state}",
           "success": "${build.success}",
           "date": "${build.date}"
       }
   }
