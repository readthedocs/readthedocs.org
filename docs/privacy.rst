Privacy Levels
==============

.. note::
    For private documentation or docs from private repositories,
    use :doc:`Read the Docs for Business </commercial/index>`.

Read the Docs supports 3 different privacy levels on 2 different objects;
Public, Private on Projects and Versions.

Understanding the Privacy Levels
--------------------------------

+------------+------------+-----------+-----------+-------------+
| Level      | Detail     | Listing   | Search    | Viewing     |
+============+============+===========+===========+=============+
| Private    | No         | No        | No        | Yes         |
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

Private
~~~~~~~

Private objects are available only to people who have permissions to see them.
They will not display on any list view, and will 404 when you link them to others.
