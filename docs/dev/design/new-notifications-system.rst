Notification system: a new approach after lot of discussions
============================================================

Notifications have been a recurrent topic in the last years.
We have talked about different problems and solution's approaches during these years.
However, due to the complexity of the change, and without having a clear path, it has been hard to prioritize.

We've written a lot about the problems and potential solutions for the current notification system.
This is a non-complete list of them just for reference:

* https://github.com/readthedocs/readthedocs.org/issues/4226
* https://github.com/readthedocs/readthedocs.org/issues/3399
* https://github.com/readthedocs/meta/discussions/126
* https://github.com/readthedocs/readthedocs.org/issues/5909
* https://github.com/readthedocs/readthedocs.org/issues/9110
* https://github.com/readthedocs/readthedocs.org/issues/9279
* https://github.com/readthedocs/readthedocs.org/issues/4235

At the offsite in Portland, Anthony and myself were able to talk deeply about this and wrote a bunch of thoughts in a Google Doc.
We had pretty similar ideas and we thought we were solving most of the problems we identified already.

I read all of these issues and all the discussions I found and wrote this document that summarizes my proposal:
*create a new notification system that we can customize and expand as we need in the future*:

* A Django model to store the notifications' data
* API endpoints to retrieve the notifications for a particular resource (User, Build, Project, Organization)
* Frontend code to display them (*outside the scope of this document*)


Goals
-----

* Keep raising exceptions for errors from the build process
* Ability to add non-error notifications from the build process
* Add extra metadata associated to the notification: icon, header, body, etc
* Support different types of notifications (e.g. error, warning, note, tip)
* Reuse the new notification system for product updates (e.g. new features, deprecated config keys)
* Message content lives on Python classes that can be translated and formatted with objects (e.g. Build, Project)
* Message could have richer content (e.g. HTML code) to generate links and emphasis
* Notifications have trackable state (e.g. unread (default)=never shown, read=shown, dismissed=don't show again, cancelled=auto-removed after user action)
* An object (e.g. Build, Organization) can have more than 1 notification attached
* Remove hardcoded notifications from the templates
* Notifications can be attached to Project, Organization, Build and User models
* Specific notifications can be shown under the user's bell icon
* Easy way to cleanup notification on status changes (e.g. subscription failure notification is auto-deleted after CC updated)
* Notifications attached to Organization/Project disappear for all the users once they are dismissed by anyone


Non-goals
---------

* Create new Build "state" or "status" option for these fields
* Implement the new notification in the old dashboard
* Define front-end code implementation
* Replace email or webhook notifications


Small notes and other considerations
------------------------------------

* Django message system is not enough for this purpose.
* Use a new model to store all the required data (expandable in the future)
* How do we handle translations?
  We should use ``_("This is the message shown to the user")`` in Python code and return the proper translation when they are read.
* Reduce complexity on ``Build`` object (remove ``Build.status`` and ``Build.error`` fields among others).
* Since the ``Build`` object could have more than 1 notification, when showing them, we will sort them by importance: errors, warnings, note, tip.
* In case we need a pretty specific order, we can add an extra field for that, but it adds unnecessary complexity at this point.
* For those notifications that are attached to the ``Project`` or ``Organization``, should it be shown to all the members even if they don't have admin permissions?
  If yes, this is good because all of them will be notified but only some of them will be able to take an action.
  If no, non-admin users won't see the notification and won't be able to communicate this to the admins
* Notification could be attached to a ``BuildCommand`` in case we want to display a specific message on a command itself.
  We don't know how useful this will be, but it's something we can consider in the future.
* Notification preferences: what kind of notifications I want to see in my own bell icon?

  - Build errors
  - Build tips
  - Product updates
  - Blog post news
  - Organization updates
  - Project updates


Implementation ideas
--------------------

This section shows all the classes and models involved for the notification system as well as some already known use-cases.

.. note:: Accessing the database from the build process

    Builders doesn't have access to the database due to security reasons.
    We had solved this limitation by creating an API endpoint the builder hits once they need to interact with the database to get a ``Project``, ``Version`` and ``Build`` resources, create a ``BuildCommand`` resource, etc.

    Besides, the build process is capable to trigger Celery tasks that are useful for managing more complex logic
    that also require accessing from and writing to the database.

    Currently, ``readthedocs.doc_builder.director.Director`` and
    ``readthedocs.doc_builder.environments.DockerBuildEnvironment``
    have access to the API client and can use it to create the ``Notification`` resources.

    I plan to use the same pattern to create ``Notification`` resources by hitting the API from the director or the build environment.
    In case we require hitting the API from other places, we will need to pass the API client instance to those other classes as well.



``Message`` class definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This class encapsulates the content of the notification (e.g. header, body, icon, etc) --the message it's shown to the uer--,
and some helper logic to return in the API response.

.. code-block:: python

    class Message:
        def __init__(self):
            header = str
            body = str
            icon = str
            icon_style = str(SOLID, DUOTONE)
            type = str(ERROR, WARNING, NOTE, TIP)

        def get_display_icon(self):
            if self.icon:
                return self.icon

            if self.type == ERROR:
                return "fa-exclamation"
            if self.type == WARNING:
                return "fa-triangle-exclamation"


Definition of notifications to display to users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This constant defines all the possible notifications to be displayed to the user.
Each notification has to be defined here using the ``Message`` class previously defined.

.. code-block:: python

    NOTIFICATION_MESSAGES = {
        "generic-with-build-id": Message(
            header=_("Unknown problem"),
            # Note the message receives the instance it's attached to
            # and could be use it to inject related data
            body=_(
                """
          There was a problem with Read the Docs while building your documentation.
          Please try again later.
          If this problem persists,
          report this error to us with your build id ({instance[pk]}).
        """,
                type=ERROR,
            ),
        ),
        "build-os-required": Message(
            header=_("Invalid configuration"),
            body=_(
                """
          The configuration key "build.os" is required to build your documentation.
          <a href='https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os'>Read more.</a>
        """,
                type=ERROR,
            ),
        ),
        "cancelled-by-user": Message(
            header=_("User action"),
            body=_(
                """
          Build cancelled by the user.
        """,
                type=ERROR,
            ),
        ),
        "os-ubuntu-18.04-deprecated": Message(
            header=_("Deprecated OS selected"),
            body=_(
                """
          Ubuntu 18.04 is deprecated and will be removed soon.
          Update your <code>.readthedocs.yaml</code> to use a newer image.
        """,
                type=TIP,
            ),
        ),
    }



``Notification`` model definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This class is the representation of a notification attached to an resource (e.g. User, Build, etc) in the database.
It contains an identifier (``message_id``) pointing to one of the messages defined in the previous section (key in constant ``NOTIFICATION_MESSAGES``).

.. code-block:: python

    import textwrap
    from django.utils.translation import gettext_noop as _


    class Notification(TimeStampedModel):
        # Message identifier
        message_id = models.CharField(max_length=128)

        # UNREAD: the notification was not shown to the user
        # READ: the notification was shown
        # DISMISSED: the notification was shown and the user dismissed it
        # CANCELLED: removed automatically because the user has done the action required (e.g. paid the subscription)
        state = models.CharField(
            choices=[UNREAD, READ, DISMISSED, CANCELLED],
            default=UNREAD,
            db_index=True,
        )

        # Makes the notification impossible to dismiss (useful for Build notifications)
        dismissable = models.BooleanField(default=False)

        # Show the notification under the bell icon for the user
        news = models.BooleanField(default=False, help_text="Show under bell icon")

        # Notification attached to
        #
        # Uses ContentType for this.
        # https://docs.djangoproject.com/en/4.2/ref/contrib/contenttypes/#generic-relations
        #
        attached_to_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        attached_to_id = models.PositiveIntegerField()
        attached_to = GenericForeignKey("attached_to_content_type", "attached_to_id")

        # If we don't want to use ContentType, we could define all the potential models
        # the notification could be attached to
        #
        # organization = models.ForeignKey(Organization, null=True, blank=True, default=None)
        # project = models.ForeignKey(Project, null=True, blank=True, default=None)
        # build = models.ForeignKey(Build, null=True, blank=True, default=None)
        # user = models.ForeignKey(User, null=True, blank=True, default=None)

        def get_display_message(self):
            return textwrap.dedent(
                NOTIFICATION_MESSAGES.get(self.message_id).format(
                    instance=self.attached_to,  # Build, Project, Organization, User
                )
            )


Attach error ``Notification`` during the build process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

During the build, we will keep raising exceptions to both things:

- stop the build process immediately
- communicate back to the ``doc_builder.director.Director`` class the build failed.

The director is the one in charge of creating the error ``Notification``,
in a similar way it currently works now.
The only difference is that instead of saving the error under ``Build.error`` as it currently works now,
it will create a ``Notification`` object and attach it to the particular ``Build``.
Note the director does not have access to the DB, so it will need to create/associate the object via an API endpoint/Celery task.

Example of how the exception ``BuildCancelled`` creates an error ``Notification``:


.. code-block:: python

    class UpdateDocsTask(...):
        def on_failure(self):
            self.data.api_client.build(self.data.build["id"]).notifications.post(
                {
                    "message_id": "cancelled-by-user",
                    # Override default fields if required
                    "type": WARNING,
                }
            )



Attach non-error ``Notification`` during the build process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

During the build, we will be able attach non-error notifications with the following pattern:

- check something in particular (e.g. using a deprecated key in ``readthedocs.yaml``)
- create a non-error ``Notification`` and attach it to the particular ``Build`` object

.. code-block:: python

    class DockerBuildEnvironment(...):
        def check_deprecated_os_image(self):
            if self.config.build.os == "ubuntu-18.04":
                self.api_client.build(self.data.build["id"]).notifications.post(
                    {
                        "message_id": "os-ubuntu-18.04-deprecated",
                    }
                )



Show a ``Notification`` under the user's bell icon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we want to show a notification on a user's profile,
we can create the notification as follows,
maybe from a simple script ran in the Django shell's console
after publishing a blog post:


.. code-block:: python

    users_to_show_notification = User.objects.filter(...)

    for user in users_to_show_notification:
        Notification.objects.create(
            message_id="blog-post-beta-addons",
            dismissable=True,
            news=True,
            attached_to=User,
            attached_to_id=user.id,
        )


Remove notification on status change
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When we show a notification for an unpaid subscription,
we want to remove it once the user has updated and paid the subscription.
We can do this with the following code:


.. code-block:: python

    @handler("customer.subscription.updated", "customer.subscription.deleted")
    def subscription_updated_event(event):
        if subscription.status == ACTIVE:
            organization = Organization.objects.get(slug="read-the-docs")

            Notification.objects.filter(
                message_id="subscription-update-your-cc-details",
                state__in=[UNREAD, READ],
                attached_to=Organization,
                attached_to_id=organization.id,
            ).update(state=CANCELLED)



API definition
--------------

I will follows the same pattern we have on APIv3 that uses nested endpoints.
This means that we will add a ``/notifications/`` postfix to most of the resource endpoints
where we want to be able to attach/list notifications.

Notifications list
~~~~~~~~~~~~~~~~~~

.. http:get:: /api/v3/users/(str:user_username)/notifications/

    Retrieve a list of all the notifications for this user.

.. http:get:: /api/v3/projects/(str:project_slug)/notifications/

    Retrieve a list of all the notifications for this project.

.. http:get:: /api/v3/organizations/(str:organization_slug)/notifications/

    Retrieve a list of all the notifications for this organization.

.. http:get:: /api/v3/projects/(str:project_slug)/builds/(int:build_id)/notifications/

    Retrieve a list of all the notifications for this build.

    **Example response**:

    .. sourcecode:: json

        {
            "count": 25,
            "next": "/api/v3/projects/pip/builds/12345/notifications/?unread=true&sort=type&limit=10&offset=10",
            "previous": null,
            "results": [
                {
                    "message_id": "cancelled-by-user",
                    "state": "unread",
                    "dismissable": false,
                    "news": false,
                    "attached_to": "build",
                    "message": {
                        "header": "User action",
                        "body": "Build cancelled by the user.",
                        "type": "error",
                        "icon": "fa-exclamation",
                        "icon_style": "duotone",
                    }
                }
            ]
        }

    :query boolean unread: return only unread notifications
    :query string type: filter notifications by type (``error``, ``note``, ``tip``)
    :query string sort: sort the notifications (``type``, ``date`` (default))


Notification create
~~~~~~~~~~~~~~~~~~~


.. http:post:: /api/v3/projects/(str:project_slug)/builds/(int:build_id)/notifications/

    Create a notification for the resource.
    In this example, for a ``Build`` resource.

    **Example request**:

    .. sourcecode:: json

        {
            "message_id": "cancelled-by-user",
            "type": "error",
            "state": "unread",
            "dismissable": false,
            "news": false,
        }


.. note::

   Similar API endpoints will be created for each of the resources
   we want to attach a ``Notification`` (e.g. ``User``, ``Organization``, etc)


Notification update
~~~~~~~~~~~~~~~~~~~


.. http:patch:: /api/v3/projects/(str:project_slug)/builds/(int:build_id)/notifications/(int:notification_id)/

    Update an existing notification.
    Mainly used to change the state from the front-end.

    **Example request**:

    .. sourcecode:: json

        {
            "state": "read",
        }


.. note::

   Similar API endpoints will be created for each of the resources
   we want to attach a ``Notification`` (e.g. ``User``, ``Organization``, etc)


Backward compatibility
----------------------

It's not strictly required, but if we want, we could extract the current notification logic from:

* Django templates

  * "Don't want ``setup.py`` called?"
  * ``build.image`` config key is deprecated
  * Configuration file is required
  * ``build.commands`` is a beta feature

* ``Build.error`` fields

  * Build cancelled by user
  * Unknown exception
  * ``build.os`` is not found
  * No config file
  * No checkout revision
  * Failed when cloning the repository
  * etc

and iterate over all the ``Build`` objects to create a ``Notification`` object for each of them.

I'm not planning to implement the "new notification system" in the old templates.
It doesn't make sense to spend time in them since we are deprecating them.

Old builds will keep using the current notification approach based on ``build.error`` field.
New builds won't have ``build.error`` anymore and they will use the new notification system on ext-theme.
