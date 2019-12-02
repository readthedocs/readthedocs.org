Sharing
=======

.. note::

   This feature only exists on `Read the Docs for Business <https://readthedocs.com/>`__.

You can share your project with users outside of your company:

* by sending them a *secret link*,
* by giving them a *password*.

These methods will allow them to view a specific project inside your company.

Additionally, you can use a HTTP Authorization Header.
This is useful to have access from a script.

Enabling
--------

* Go into your *Project Admin* page and to the *Sharing* menu.
* Under the *Share with someone new* heading, select the way you prefer (secret link, password, or HTTP header token),
  add an expiration date and a *Description* so you remember who you're sharing it with.
* Click *Share!* to create.
* Get the info needed to share your documentation with other users:

  * If you have selected secret link, copy the link that is generated
  * In case of password, copy the link and password
  * For HTTP header token, you need to pass the ``Authorization`` header in your HTTP request.

* Give that information to the person who you want to give access.

.. note::
   
   You can always revoke access in the same panel.

Effects
-------

Secret Link
***********

Once the person you send the link to clicks the link,
they will have access to view your project.

Password
********

Once the person you send the link to clicks on the link, they will see
an *Authorization required* page asking them for the password you
generated. When the user enters the password, they will have access to
view your project.

HTTP Authorization Header
*************************

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
