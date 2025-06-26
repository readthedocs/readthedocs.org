Pull request diff
=================

Get a list of documentation files that changed between the pull request and the latest version of the documentation,
and see their differences highlighted visually on the documentation pages.

While it's helpful to see the changes in source files,
it can be difficult to understand how those changes will look in the rendered documentation,
or their impact in the documentation as a whole.
Read the Docs makes it easy to see the changes in the rendered documentation.

.. figure:: /img/screenshot-viz-diff-ui.png
   :width: 80%

Configuration
-------------

The following options are available:

Show diff menu in preview
~~~~~~~~~~~~~~~~~~~~~~~~~

Addon (TBD)

When enabnled, a new UI element appears at the top right of the page showing a dropdown selector containing all the files that have changed in that pull request build.

.. figure:: /img/screenshot-viz-diff-ui.png
   :width: 80%

You can select any of those files from the dropdown to jump directly into that page.
Once there, you can toggle visual diff on and off by pressing the :guilabel:`Show diff` link from the UI element, or pressing the `d` key if you have hotkeys enabled.

Visual diff will show all the sections that have changed and their differences highlighted with red/green background colors.
Then you can jump between each of these chunks by clinking on the up/down arrows.

Show diff in the pull request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBD

Base version
~~~~~~~~~~~~

The base version is the version of the documentation that is used to compare against the pull request.
By default, this is the latest version of the documentation.

Ignore files
~~~~~~~~~~~~

Patterns are matched against the relative paths of the HTML files produced by the build,
you should try to match ``index.html``, not ``docs/index.rst``, nor ``/en/latest/index.html``.
Patterns can include one or more of the following special characters:

- ``*`` matches everything, including slashes.
- ``?`` matches any single character.
- ``[seq]`` matches any character in ``seq``.

Limitations and known issues
----------------------------

- Only HTML files are taken into consideration for the diff.
- The diff is done between the files from the latest successful build of the pull request and the default base version (latest by default).
  If your pull request get's out of sync with the branch it is based on, the diff may not be accurate, and may show unrelated files an sections as changed.
- The diff is done by comparing the "main content" of the HTML files.
  This means that some changes outside the main content, like header or footer, may not be detected.
  This is done to avoid showing changes that are not relevant to the documentation content itself.
  Like all pages being marked as changed because of a date or commmit hash being updated in the footer.
- Invisible changes. Some sections may be highlighted as changed, even when they haven't actually visually changed.
  This can be due the underlying HTML changing, but there is no visual change, for example, if the URL of a link changed.
- Tables may be shown to have changes when they have not actually changed.
  This is due to subtle variations in how HTML tables are rendered, and will be fixed in a future version.
- The background of diff chunks may be incorrect when we are unable to detect the correct main parent element for the chunk.
