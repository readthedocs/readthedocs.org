Scoped API keys
===============

Goals
-----

- Allow users to generate API keys that are scoped to a project, and can be used to access the Read the Docs API.
- Prioritize allowing users to use this key with the upload API,
  so we can start testing this feature more broadly without using keys that grant access to the entire account.
- Support permissions like read-only, write, upload.
- Allow expiration of the key, and allow to regenerate a new one.
- Include a prefix to help identify the scope and the platform (community or business) the key is for.
- Make it easy to integrate or extend for future keys, like organization and user scoped keys.

Non-goals
---------

- Support API V2.
- Make use of these keys from the builders.

Backend
-------

Everything will be based on the rest-framework-api-key package,
since it provides a lot of the functionality we need, and it's already used in the build API keys.

Modeling
--------

We'll have a new model that will serve as the model for all future API keys.

.. code-block:: python

   from rest_framework_api_key.models import AbstractAPIKey

   class ProjectPermission(StrEnum):
       READ = "project:read"
       WRITE = "project:write"
       UPLOAD = "project:upload"

   class RTDAPIKey(AbstractAPIKey):
       project = models.ForeignKey(Project, on_delete=models.CASCADE)
       permissions = models.JSONField(default=list, blank=True)

In the future, when we add organization and user scoped API keys, we can add new fields to this model (``organization`` and ``user``).

Prefixes
--------

We want users to be able to identify the type of API key and what platform it is for, so we will add a prefix to the generated API key.

For keys that belong to Read the Docs Community, we will use the prefix ``rtdorg_``,
and for keys that belong to Read the Docs Business, we will use the prefix ``rtdcom_``
(another option is to use ``rtd_``/``rtdb_`` or ``rtd_``/``rtdcom_``).
In addition, we will add another prefix to identify the type of API key, e.g. ``proj_``, ``org_``, ``user_``.
We can achieve this by by extending the ``KeyGenerator`` and ``BaseAPIKeyManager`` classes.

For example:

- ``rtdorg_proj_abc123`` for a project scoped API key in Read the Docs Community.
- ``rtdcom_proj_abc123`` for a project scoped API key in Read the Docs Business.

Having prefixes will also help our own tools/scripts (like the upload client) to identify the type of API key and what platform it is for,
so we can infer what URL to use for the API, and if the project/organization should be provided or not.

Expiration
----------

Keys will have an expiration date,
but after it's set, it can't be changed for security reasons.
Keys should be able to be regenerated, which will create a new key with a new expiration date
and same permissions as the original key.

We should be able to support keys that don't expire,
but we should not encourage this, for security reasons.

Permissions
-----------

The following permissions will be available for project scoped API keys:

- ``project:read`` - Read-only access to the project and its versions.
- ``project:write`` - Read the write access to the project and its versions.
- ``project:upload`` - Access to the upload API only, no access to project or version endpoints (no even read-only access).

We'll use the ``permissions`` field in the model to store the permissions for each API key, and we can use a JSONField to store a list of permissions.
We'll have a custom permission class that will check if the key has the required permission for the endpoint/action requested.

Extra metadata
--------------

We can add extra metadata to the API key like the last time it was used,
and integrate it with our audit models, so we can expose this information to users.

Build API keys
--------------

These keys are in a weird state, since they are supposed to be scoped to a build,
but they can access project and version endpoints,
and the keys are attached to a project, and they can be used to access other builds in the same project.

These keys will be left as they are for now, but we can consider using the new ``RTDAPIKey`` model for them in the future,
and add a ``build`` field to the model.
But even then, these keys are an special case,
as they still need read-only access to project and version endpoints,
and will need to have another specialized endpoint to update the project and version information as needed,
or we can find other ways to handle this without giving the key write access to the version or project attributes directly.

Implementing project scoped API keys doesn't require any of these changes to be made, and we can implement them later.

First iteration
---------------

Support for project scoped API keys only, with the following permissions:

- ``project:upload``
- ``project:read``
- ``project:write``

Even read/write could be left for later, so we don't have to worry about checking every endpoint for the correct permission, and we can focus on the upload API only.

We won't track any extra metadata for the keys, and have a simple interface to create, list, and delete keys.
