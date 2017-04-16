Privacy Levels
==============

Read the Docs supports 3 different privacy levels on 2 different objects;
Public, Protected, Private on Projects and Versions.

Understanding the Privacy Levels
--------------------------------

+------------+------------+-----------+-----------+-------------+
| Level      | Detail     | Listing   | Search    | Viewing     |
+============+============+===========+===========+=============+
| Private    | No         | No        | No        | Yes         |
+------------+------------+-----------+-----------+-------------+
| Protected  | Yes        | No        | No        | Yes         |
+------------+------------+-----------+-----------+-------------+
| Public     | Yes        | Yes       | Yes       | Yes         |
+------------+------------+-----------+-----------+-------------+

.. note:: With a URL to view the actual documentation, even private docs are viewable.
          This is because our architecture doesn't do any logic on documentation display,
          to increase availability.

Public
~~~~~~

This is the easiest and most obvious. It is also the default.
It means that everything is available to be seen by everyone.

Protected
~~~~~~~~~

Protected means that your object won't show up in Listing Pages,
but Detail pages still work. For example, a Project that is Protected will
not show on the homepage Recently Updated list, however,
if you link directly to the project, you will get a 200 and the page will display.

Protected Versions are similar, they won't show up in your version listings,
but will be available once linked to.


Private
~~~~~~~

Private objects are available only to people who have permissions to see them.
They will not display on any list view, and will 404 when you link them to others.
