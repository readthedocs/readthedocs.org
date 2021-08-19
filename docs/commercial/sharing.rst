Sharing
=======

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.

You can share your project with users outside of your company:

* by sending them a *secret link*,
* by giving them a *password*.

These methods will allow them to view specific projects or versions of a project inside your organization.

Additionally, you can use a HTTP Authorization Header.
This is useful to have access from a script.

Enabling
--------

* Go into your project's :guilabel:`Admin` page and click on :guilabel:`Sharing`.
* Click on :guilabel:`New Share`
* Select access type (secret link, password, or HTTP header token),
  add an expiration date and a *Description* so you remember who you're sharing it with.
* Check ``Allow access to all versions?`` if you want to grant access to all versions,
  or uncheck that option and select the specific versions you want grant access to.
* Click :guilabel:`Save`.
* Get the info needed to share your documentation with other users:

  * If you have selected secret link, copy the link that is generated
  * In case of password, copy the link and password
  * For HTTP header token, you need to pass the ``Authorization`` header in your HTTP request.

* Give that information to the person who you want to give access.

.. note::
   
   You can always revoke access in the same panel.

Users can log out by using the :ref:`Log Out <versions:Logging out>` link in the RTD flyout menu.

Effects
-------

Secret Link
***********

Once the person you send the link to clicks the link,
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
generated. When the user enters the password, they will have access to
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
The header has the form ``Authorization: Token <ACCESS_TOKEN>``.
For example:

.. prompt:: bash $
   
   curl -H "Authorization: Token 19okmz5k0i6yk17jp70jlnv91v" https://docs.example.com/en/latest/example.html

Basic Authorization
~~~~~~~~~~~~~~~~~~~

You can also use basic authorization, with the token as user and an empty password.
For example:

.. prompt:: bash $
   
   curl --url https://docs.example.com/en/latest/example.html --user '19okmz5k0i6yk17jp70jlnv91v:'
