Dashboard screenshots
=====================

The user documentation includes screenshots of the dashboard.
They are generated from a local development instance with ``scripts/docs_screenshots.py``,
so anyone can reproduce or update them when the dashboard changes.

This page explains how to run the script, the conventions every screenshot follows,
and how to add a new one.

Running the script
------------------

The script uses `Playwright <https://playwright.dev/python/>`__ to open dashboard pages,
tidy them up, and save the images directly into ``docs/user/``.
Review the result with ``git diff`` or your image viewer.

#. Start the development instance you need.
   Only one instance runs at a time, so take Community and Business screenshots separately.
   See :doc:`install`.

#. Log in to the dashboard in your browser, and copy the value of the ``sessionid`` cookie.

#. Run the script:

   .. code-block:: console

      $ export RTD_COMMUNITY_SESSIONID=<sessionid from devthedocs.org>
      $ export RTD_BUSINESS_SESSIONID=<sessionid from devthedocs.com>
      $ uv run scripts/docs_screenshots.py --list
      $ uv run scripts/docs_screenshots.py
      $ uv run scripts/docs_screenshots.py redirects tutorial

   Arguments filter screenshots by their path.
   Screenshots for an instance that isn't running are skipped.

The script uses your installed Google Chrome.
If you don't have it, install Playwright's Chromium with ``uv run --with playwright playwright install chromium``.

Conventions
-----------

Every screenshot should look like it was taken by the same person on the same day.

Look
   * Light theme, regardless of your profile's theme.
   * 1280 pixels wide, at 1x scale.
     Small inline images, like icon buttons, use 2x scale.
   * Forms and lists show the whole page without the footer.
     Details, like a single field or a list of activity, are cropped to that element.
     Images shown at a small scale in the docs are cropped to the content column.
   * Highlight an element with a 3 pixel outline in ``#2185d0`` with rounded corners.

Names
   * Username: ``example-user``.
   * Project: ``docs``. In the tutorial: ``tutorial``.
   * Organizations: ``Example Docs`` and ``Example Company``.
   * Repository: ``example-user/tutorial``.
   * Avatars: the generic silhouette, ``https://assets.readthedocs.org/static/images/silhouette.png``.

Never publish
   * Real usernames, names, avatars, or organization names.
   * Development URLs (``devthedocs.org``). Use ``https://app.readthedocs.org`` instead.
   * Secrets, tokens, SSH keys, or SSH key fingerprints. Replace them with placeholders.
   * The organization and *Unofficial* badges in the project header, and the staff-only *Debug* tab.
   * Notifications unrelated to the screenshot, like *Search indexing has been disabled*.

Text
   When a screenshot changes, update the text around it to match the dashboard.
   Follow the :doc:`style-guide`: ``:menuselection:`` for navigation
   (``:menuselection:`Settings --> Redirects```) and ``:guilabel:`` for buttons and fields,
   using the exact label from the dashboard.

Sample data
-----------

The development database rarely has realistic data.
Never change the development database for a screenshot.
Instead, the script changes the page in the browser:

Edit the page
   Rename projects, replace URLs and secrets, make dates recent,
   or add rows with the same markup as the template.
   Helpers: ``tidy()``, ``replace_text()``, ``recent_times()``, ``set_counters()``.

Answer API calls
   Pages that load data with JavaScript, like the repository search in *Add project*,
   get sample data from ``fake_api()``.

Chart data
   Analytics charts read their data from an inline JSON script.
   ``chart_data()`` replaces it before the page reads it.

When a screenshot contains sample data, mention it in the pull request.

Data sources
------------

Screenshots borrow objects from your development database.
They are listed in ``SOURCES`` at the top of the script.
If your database is different, update ``SOURCES``; it should be the only change you need.

``project``
   A Community project with exactly two versions, ``latest`` and ``stable``.
``busy_project``
   A Community project with redirects, traffic and search analytics data,
   an integration with webhook calls (``busy_integration``),
   and a successful build of a standard Sphinx project (``busy_build``).
``webhook_project`` and ``webhook``
   A Community project with an outgoing webhook.
``subproject_parent``
   A Community project with one subproject.
``business_team``
   The ``data-value`` of the team to highlight in the Business *Add project* dropdown.
``business_ssh_project`` and ``business_ssh_key``
   A Business project and the ID of one of its SSH keys.
``tutorial_live_docs``
   Public documentation built from the `tutorial template <https://github.com/readthedocs/tutorial-template>`__.

Adding a screenshot
-------------------

#. Open the page on the development instance and decide what to capture.
   Look at the existing screenshot, if any, to keep the same framing.

#. Add a function decorated with ``@shot``.
   It receives a Playwright ``page``, prepares it, and returns the area to capture:

   .. code-block:: python

      @shot("img/screenshot_domains.png")
      def domains(page):
          goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/domains/")
          return above_footer(page)

   ``goto()`` already applies the conventions above.
   Use ``instance="business"`` for Business pages, and ``scale=2`` for small inline images.

#. Run the script for that screenshot only, and look at the result.
   Check for real names, development URLs, and secrets before committing.

#. Update the documentation text around the image.

Things to know
--------------

* Don't rewrite the HTML response of a page with ``page.route()``.
  Chrome then treats the page as public, and blocks the local CSS and JavaScript.
  Faking API responses (``fake_api()``) is fine.
* Semantic UI search fields only react to key presses.
  Use ``page.keyboard.type()`` instead of ``fill()``.
* Notifications are web components that render after the page loads,
  so they are hidden with CSS instead of being removed.
* Select options, like the redirect type, through the dashboard's own dropdown,
  so previews and other JavaScript react to them.
* Some features only show for specific projects.
  For example, *Show build overview in a comment* only shows for projects using the GitHub App.

Manual images
-------------

Some images can't be generated by the script, like pages on GitHub
or screenshots provided by someone else.
Edit them with `ImageMagick <https://imagemagick.org/>`__, following the same conventions.

Highlight an area
   .. code-block:: console

      $ magick in.png -fill none -stroke '#2185d0' -strokewidth 3 \
          -draw 'roundrectangle 23,108 180,155 5,5' out.png

Remove a border around a screenshot
   .. code-block:: console

      $ magick in.png -fuzz 10% -trim +repage out.png

Replace text, like a username
   #. Find the text position: crop the line and look for columns with dark pixels.
   #. Find the font size: render the original word with the same font
      (``magick -font <font> -pointsize <size> label:'word' -trim -format '%w' info:``)
      until the width matches.
   #. Cover the old text with the background color, and draw the new text on the same baseline:

      .. code-block:: console

         $ magick in.png -fill white -draw 'rectangle 238,232 540,258' \
             -font NotoSans-Regular.ttf -pointsize 16 -fill '#1f2328' \
             -draw "text 241,249 'personal account example-user'" out.png

These images are currently edited by hand:

* ``img/screenshot_rtd_downloads.png`` and ``_static/images/tutorial/flyout-downloads.png``: the flyout menu.
* ``_static/images/tutorial/github-app-install.png``: the GitHub App installation page, with the account renamed.
* ``_static/images/tutorial/github-template.png``, ``gh-edit.png``, and ``gh-pr-build.png``: GitHub pages.
