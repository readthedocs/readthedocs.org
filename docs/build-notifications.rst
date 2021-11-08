Build Notifications and Webhooks
================================

.. note::

   Currently we don't send notifications or trigger webhooks
   on :doc:`builds from pull requests </pull-requests>`.

Email notifications
-------------------

Read the Docs allows you to configure emails that can be sent on failing builds.
This makes sure you know when your builds have failed.

Take these steps to enable build notifications using email:

* Go to :guilabel:`Admin` > :guilabel:`Notifications` in your project.
* Fill in the **Email** field under the **New Email Notifications** heading
* Submit the form

You should now get notified by email when your builds fail!

Build Status Webhooks
---------------------

Read the Docs can also send webhooks when builds are triggered, successful or failed.

Take these steps to enable build notifications using a webhook:

* Go to :guilabel:`Admin` > :guilabel:`Webhooks` in your project.
* Fill in the **URL** field and select what events will trigger the webhook
* Modify the payload or leave the default (see below)
* Click on :guilabel:`Save`

.. figure:: /_static/images/webhooks-events.png
   :align: center
   :alt: URL and events for a webhook

   URL and events for a webhook

Every time one of the checked events triggers,
Read the Docs will send a POST request to your webhook URL.
The default payload will look like this:

.. code-block:: json

   {
       "event": "build:triggered",
       "name": "docs",
       "slug": "docs",
       "version": "latest",
       "commit": "2552bb609ca46865dc36401dee0b1865a0aee52d",
       "build": "15173336",
       "start_date": "2021-11-03T16:23:14",
       "build_url": "https://readthedocs.org/projects/docs/builds/15173336/",
       "docs_url": "https://docs.readthedocs.io/en/latest/"
   }

When a webhook is sent, a new entry will be added to the
"Recent Activity" table. By clicking on each individual entry,
you will see the server response, the webhook request, and the payload.

.. figure:: /_static/images/webhooks-activity.png
   :align: center
   :alt: Activity of a webhook

   Activity of a webhook

Custom payload examples
~~~~~~~~~~~~~~~~~~~~~~~

You can customize the payload of the webhook to suit your needs,
as long as it is valid JSON. Below you have a couple of examples,
and in the following section you will find all the available variables.

.. figure:: /_static/images/webhooks-payload.png
   :width: 80%
   :align: center
   :alt: Custom payload

   Custom payload

Slack
+++++

.. code-block:: json

   {
     "attachments": [
       {
         "color": "#db3238",
         "blocks": [
           {
             "type": "section",
             "text": {
               "type": "mrkdwn",
               "text": "*Read the Docs build failed*"
             }
           },
           {
             "type": "section",
             "fields": [
               {
                 "type": "mrkdwn",
                 "text": "*Project*: <{{ project.url }}|{{ project.name }}>"
               },
               {
                 "type": "mrkdwn",
                 "text": "*Version*: {{ version.name }} ({{ build.commit }})"
               },
               {
                 "type": "mrkdwn",
                 "text": "*Build*: <{{ build.url }}|{{ build.id }}>"
               }
             ]
           }
         ]
       }
     ]
   }

More information on `the Slack Incoming Webhooks documentation <https://api.slack.com/messaging/webhooks>`_.

Discord
+++++++

.. code-block:: json

   {
     "username": "Read the Docs",
     "content": "Read the Docs build failed",
     "embeds": [
       {
         "title": "Build logs",
         "url": "{{ build.url }}",
         "color": 15258703,
         "fields": [
           {
             "name": "*Project*",
             "value": "{{ project.url }}",
             "inline": true
           },
           {
             "name": "*Version*",
             "value": "{{ version.name }} ({{ build.commit }})",
             "inline": true
           },
           {
             "name": "*Build*",
             "value": "{{ build.url }}"
           }
         ]
       }
     ]
   }

More information on `the Discord webhooks documentation <https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks>`_.

Variable substitutions reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``{{ event }}``
  Event that triggered the webhook, one of ``build:triggered``, ``build:failed``, or ``build:passed``.

``{{ build.id }}``
  Build ID.

``{{ build.commit }}``
  Commit corresponding to the build, if present (otherwise ``""``).

``{{ build.url }}``
  URL of the build, for example ``https://readthedocs.org/projects/docs/builds/15173336/``.

``{{ build.docs_url }}``
  URL of the documentation corresponding to the build,
  for example ``https://docs.readthedocs.io/en/latest/``.

``{{ build.start_date }}``
  Start date of the build (UTC, ISO format), for example ``2021-11-03T16:23:14``.

``{{ organization.name }}``
  Organization name (Commercial only).

``{{ organization.slug }}``
  Organization slug (Commercial only).

``{{ project.slug }}``
  Project slug.

``{{ project.name }}``
  Project name.

``{{ project.url }}``
  URL of the project :term:`dashboard`.

``{{ version.slug }}``
  Version slug.

``{{ version.name }}``
  Version name.

Validating the payload
~~~~~~~~~~~~~~~~~~~~~~

After you add a new webhook, Read the Docs will generate a secret key for it
and uses it to generate a hash signature (HMAC-SHA256) for each payload
that is included in the ``X-Hub-Signature`` header of the request.

.. figure:: /_static/images/webhooks-secret.png
   :width: 80%
   :align: center
   :alt: Webhook secret

   Webhook secret

We highly recommend using this signature
to verify that the webhook is coming from Read the Docs.
To do so, you can add some custom code on your server,
like this:

.. code-block:: python

   import hashlib
   import hmac
   import os


   def verify_signature(payload, request_headers):
       """
       Verify that the signature of payload is the same as the one coming from request_headers.
       """
       digest = hmac.new(
           key=os.environ["WEBHOOK_SECRET"].encode(),
           msg=payload.encode(),
           digestmod=hashlib.sha256,
       )
       expected_signature = digest.hexdigest()

       return hmac.compare_digest(
           request_headers["X-Hub-Signature"].encode(),
           expected_signature.encode(),
       )

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

To migrate to the new webhooks and keep a similar structure,
you can use this payload:

.. code-block:: json

   {
       "name": "{{ project.name }}",
       "slug": "{{ project.slug }}",
       "build": {
           "id": "{{ build.id }}",
           "commit": "{{ build.commit }}",
           "state": "{{ event }}",
           "date": "{{ build.start_date }}"
       }
   }
