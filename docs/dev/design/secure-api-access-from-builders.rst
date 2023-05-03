Secure API access from builders
===============================

Goals
-----

- Provide a secure way for builders to access the API.
- Limit the access of the tokens to the minimum required.

Non-goals
---------

- Migrate builds to use API V3
- Implement this mechanism in API V3
- Expose it to users

All these changes can be made in the future, if needed.

Current state
-------------

Currently, we access the API V2 from the builders using the credentials of the "builder" user.
This user is a superuser, it has access to all projects,
write access to the API, access to restricted endpoints, and restricted fields.

The credentials are hardcoded in our settings file,
so if there is a vulnerability that allows users to have access to the settings file,
the attacker will have access to the credentials of the "builder" user,
giving them full access to the API and all projects.

Proposed solution
-----------------

Instead of using the credential of a super user to access the API,
we will create a temporal token attached to a project, and one of the owners of the project.
This way this token will have access to the given project only for a limited period of time.

This token will be generated from the webs,
and passed to the builders via the celery task,
where it can be used to access the API.
Once the build has finished, this token will be revoked.

Technical implementation
------------------------

We will use the rest-knox_ package,
this package is recommended by the DRF documentation,
since the default token implementation of DRF is very basic,
some relevant features of knox are:

- Support for several tokens per user.
- Tokens are stored in a hashed format in the database.
  We don't have access the tokens after they are created.
- Tokens can hava an expiration date.
- Tokens can be created with a prefix (rtd_xxx) (unreleased)
- Support for custom token model (unreleased)

We won't expose the token creation view directly,
since we can create the tokens from the webs,
and this isn't exposed to users.

The view to revoke the token will be exposed,
since we need it to revoke the token once the build has finished.

From the API, we just need to add the proper permission and authentication classes
to the views we want to support.

To differentiate from a normal user and a token authed user,
we will have access to the token via the ``request.auth`` attribute in the API views,
this will also be used to get the attached projects to filter the querysets.

The knox package allows us to provide our own token model,
this will be useful to add our own fields to the token model.
Fields like the projects attached to the token,
or access to all projects the user has access to, etc.

.. _rest-knox: https://james1345.github.io/django-rest-knox/

Flow
----

The flow of creation and usage of the token will be:

- Create a token from the webs when a build is triggered.
  The triggered project will be attached to the token,
  if the build was triggered by a user, that user will be attached to the token,
  otherwise the token will be attached to one of the owners of the project.
- The token will be created with an expiration date
  of 3 hours, this should be enough for the build to finish.
  We could also make this dynamic depending of the project.
- Pass the token to the builder via the celery task.
- Pass the token to all places where the API is used.
- Revoke the token when the build has finished.
  This is done by hitting the revoke endpoint.
- In case the revoke endpoint fails, the token will expire in 3 hours.

Why attach tokens to users?
---------------------------

Attaching tokens to users will ease the implementation,
since we can re-use the code from knox package.

Attaching tokens to projects only is possible,
but it will require to manage the authentication manually.

Kepping backwards compatibility
-------------------------------

Access to write API V2 is restricted to superusers,
and was used only from the builders.
So we don't need to keep backwards compatibility for authed requests,
but we need to keep the old implementation working while we deploy the new one.

Possible issues
---------------

Some of the features that we may need are not released yet,
we need the custom token model feature, specially.

There is a race condition when using the token,
and the user that is attached to that token is removed from the project.
This is, if the user is removed while the build is running,
the builders won't be able to access the API.

Future work
-----------

This work can be extended to API V3, and be exposed to users in the future.
We only need to take into consideration that the token model will be shared by both,
API V2 and API V3.
