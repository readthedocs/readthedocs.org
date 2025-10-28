Sharing private documentation
=============================

.. include:: /shared/admonition-rtd-business.rst

Sharing private documentation is useful for giving quick access to your documentation to users outside of your organization.
It allows you to share specific projects or versions of a project with users who don't have access to your organization.

Common sharing use cases include:

* Sharing a project with contractors or partners.
* Sharing documentation for your product only to specific customers.
* Embedding documentation in a SaaS application dashboard.

Creating a shared item
----------------------

* Go into your project's :guilabel:`Admin` page and click on :guilabel:`Sharing`.
* Click on :guilabel:`New Share`
* Select access type (secret link, password, or HTTP header token),
  add an expiration date and a *Description* to help with managing access in the future.
* Check ``Allow access to all versions?`` if you want to grant access to all versions,
  or uncheck that option and select the specific versions you want to grant access to.
* Click :guilabel:`Save`.
* Get the info needed to share your documentation with other users:

  * **Secret link:** copy the link that is generated
  * **Password:** copy the link and password
  * **HTTP header token**: Copy the token, and then pass the ``Authorization`` header in your HTTP request.

* Give that information to the person who you want to give access.

.. note::

   You can always revoke access by removing the sharing item on this page.

Sharing methods
---------------

Secret link
***********

Once the person you send the link to clicks it,
they will have access to the documentation while their browser window is open.

If you want to link to a specific page,
you can do this by passing the ``next`` query parameter in the URL.
For example ``https://mydocs.readthedocs-hosted.com/_/sharing/xxxxxxxxx?next=/en/latest/page.html``.

.. tip::
   This is useful for sharing access to an entire set of documentation for a user.
   You can embed these links in an internal wiki, for example,
   and all your employees will be able to browse the docs without a login.

Password
********

Once the person you send the link to clicks on the link, they will see
an *Authorization required* page asking them for the password you
generated. When the user enters the password, they will gain access to
view your project.

.. tip::
   This is useful for when you have documentation you want users to bookmark.
   They can enter a URL directly and enter the password when prompted.

HTTP Authorization Header
*************************

.. tip::
   This approach is useful for automated scripts.
   It only allows access to a page when the header is present,
   so it doesn't allow browsing docs inside of a browser.

Token Authorization
~~~~~~~~~~~~~~~~~~~

You need to send the ``Authorization`` header with the token on each HTTP request.
The header has the form ``Authorization: Token <TOKEN>``.
For example:

.. prompt:: bash $

   curl -H "Authorization: Token $TOKEN" https://docs.example.com/en/latest/example.html

Basic Authorization
~~~~~~~~~~~~~~~~~~~

You can also use basic authorization, with the token as user and an empty password.
For example:

.. prompt:: bash $

   curl --url https://docs.example.com/en/latest/example.html --user '$TOKEN:'

Typical sharing configurations
------------------------------

There are a few common ways to architect sharing,
with trade-offs between them,
and you should choose the one that best fits your use case.

Bulk passwords
**************

If you want to limit access to a group of users,
you can create a password for each user,
and then share the password with them.
This allows users to access the documentation directly,
but requires more management on your end.
Any time a new user needs access or you want to remove access,
you will need to generate a new password for them.

Authenticated redirect
**********************

If you want to share documentation with a group of users,
you need to authenticate those users against your own system first.
The simplest way to do this is to create an authenticated redirect on your site,
which then redirects to the Read the Docs :ref:`commercial/sharing:secret link`.

This should require minimal customization,
and will ensure that only authenticated users can access the documentation.
The downside is that users won't be able to access the documentation directly from a bookmark,
and will have to go through your site first.

Authenticated proxy
*******************

If you want a more transparent experience for your users,
you can create a proxy that authenticates users against your system,
and then proxies the request to Read the Docs.
This is more complex to set up,
but will allow users to access the documentation directly from a bookmark.

This approach would use a :ref:`commercial/sharing:HTTP Authorization Header` to authenticate users,
and would be configured in your proxy server.

Proxy example
-------------

Below is an example of how to configure Nginx to proxy requests to Read the Docs while adding the token in the `Authorization` header.

.. code-block:: nginx

   server {
       listen 80;
       server_name docs.example.com;

       location / {
           proxy_pass https://docs-example.readthedocs-hosted.com;

           # Add Authorization header with the token
           proxy_set_header Authorization "Token <TOKEN>";

           # Optionally forward other headers
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
