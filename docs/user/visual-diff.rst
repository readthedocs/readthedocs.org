Visual diff
===========

Get a list of documentation files that changed between the :doc:`pull request </pull-requests>` and the latest version of the documentation,
and see their differences highlighted visually on the documentation pages.

While seeing changes in source files is helpful,
it can be difficult to understand how those changes will look in the rendered documentation,
or their impact on the documentation as a whole.
Read the Docs makes it easy to see the changes in the rendered documentation.

Show diff menu in preview
-------------------------

To enable or disable this feature for your project:

#. Go the :guilabel:`Settings` tab of your project.
#. Click on :guilabel:`Addons`, and click on :guilabel:`Visual diff`.
#. Check or uncheck the :guilabel:`Enable visual diff` option.
#. Click on :guilabel:`Save`.

When enabled, a new UI element appears at the top right of the page showing a dropdown selector containing all the files that have changed in that pull request build.

.. figure:: /img/screenshot-viz-diff-ui.png
   :width: 80%

You can select any of those files from the dropdown to jump directly into that page.
Once there, you can toggle Visual Diff on and off by pressing the :guilabel:`Show diff` link from the UI element, or pressing the ``d`` key if you have hotkeys enabled.

Visual diff shows all the sections that have changed, highlighting their differences with red/green background colors.
You can jump between each of these chunks by clinking on the up/down arrows.

Show build overview in pull requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   This feature is only available for projects connected to a :ref:`reference/git-integration:GitHub App`.

To enable or disable this feature for your project:

#. Go the :guilabel:`Settings` tab of your project.
#. Click on :guilabel:`Pull request builds`.
#. Check or uncheck the :guilabel:`Show build overview in a comment` option.
#. Click on :guilabel:`Update`.

When enabled, a comment is added to the pull request when changes are detected between the pull request and the latest version of the documentation.

.. figure:: /img/build-overview-comment.png

General settings
----------------

Ignored files
~~~~~~~~~~~~~

You can configure a list of files or patterns to be ignored when listing the files that changed in the pull request.
This is useful when you have files that have a date in them,
or listing/archive files that show changes without content changes in those files.

#. Go the :guilabel:`Settings` tab of your project.
#. Click on :guilabel:`Addons`, and click on :guilabel:`File tree diff`.
#. In the :guilabel:`Ignored files` field, add one or more patterns to ignore, one per line.
#. Click on :guilabel:`Save`.

Patterns are matched against the relative paths of the HTML files produced by the build,
you should try to match ``index.html``, not ``docs/index.rst``, nor ``/en/latest/index.html``.
Patterns can include one or more of the following special characters:

- ``*`` matches everything, including slashes.
- ``?`` matches any single character.
- ``[seq]`` matches any character in ``seq``.

Base version
~~~~~~~~~~~~

The base version is the version of the documentation that is used to compare against the pull request.
By default, this is the ``latest`` version of the documentation.
This is useful if your ``latest`` version doesn't point the default branch of your repository.

.. note::

   This option can be changed by contacting :doc:`/support`.

How main content is detected
----------------------------

The visual diff compares the "main content" of HTML pages,
ignoring headers, footers, navigation, and other page elements that aren't part of the documentation content itself.
This helps avoid false positives, like all pages being marked as changed because of a date or commit hash being updated in the footer.

For details on how the main content area is detected,
see :ref:`reference/main-content-detection:detection logic`.

.. tip::

  If the heuristic root element picked by Visual Diff is wrong for your project theme, set the :guilabel:`CSS main content selector` under :guilabel:`Settings > Addons`. Visual Diff honors this override; other features like Server Side Search do not.

Limitations and known issues
----------------------------

- The diff considers HTML files only.
- The diff is done between the files from the latest successful build of the pull request and the default base version (latest by default).
  If your pull request gets out of sync with its base branch, the diff may not be accurate, and may show unrelated files and sections as changed.
- Invisible changes. Some sections may be highlighted as changed, even when they haven't actually visually changed.
  This can happen when the underlying HTML changes without a corresponding visual change, for example, if a link's URL is updated
- Tables may be shown to have changes when they have not actually changed.
  This is due to subtle variations in how HTML tables are rendered, and will be fixed in a future version.
- The background of diff chunks may be incorrect when we are unable to detect the correct main parent element for the chunk.
