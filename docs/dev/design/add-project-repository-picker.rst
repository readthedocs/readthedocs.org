Repository picker for "Add project"
===================================

The "Add project" page asks the user to pick one repository from their connected accounts,
and the page doesn't make that obvious.
The only control is a search input styled like a list filter.
Below it sits a large placeholder box whose whole message is to use the search above.
The biggest thing on the page is empty and the smallest thing is the only thing that works.

Problem
-------

Picking a repository has three parts, and the page only serves the first one well:

Find it
   Users with a handful of repos want to see them.
   Users with hundreds want to type a name.
   Users who came from GitHub already have the URL.

Check it
   Before continuing, the user needs to know if the repo is private,
   if they have admin rights on it, and if it's already imported.
   Today that shows in a card only after selection,
   and in small icons in the dropdown one hover at a time.

Fix it when it's missing
   Repos are missing because the GitHub App wasn't granted access, or the list is stale.
   That help lives in a popup that appears after a few failed searches, then a modal.

The dropdown makes the second and third parts worse.
Results vanish on blur, so the user can't compare two repos or read the state icons at leisure,
and the empty state has nowhere to put the repair actions except a popup.

Options
-------

Keep the search dropdown, make it the hero
   Bigger input, a real heading, results open on focus, and the placeholder box removed.
   Cheapest by far and keeps all the current JS.
   It doesn't fix the transient results or the hidden repair flow, so it's a polish on the wrong shape.
   Worth doing only as a stopgap.

A list with a filter
   Render the repositories as a list on page load,
   with a filter input at the top and a Continue button on each row.
   The private, admin, and already-imported states become labels on the row, visible all at once.
   The empty state becomes a normal placeholder with the resync and GitHub App buttons in it, instead of a popup.

   The cost is pagination: the API returns 10 per page, so a user with 300 repos pages or types.
   That's fine, since anyone with 300 repos already knows the name.
   The bigger cost is that the current dropdown code,
   including the Knockout result template and the popup logic,
   gets replaced rather than reused.

Group by account and organization
   A sidebar of connected accounts and their organizations,
   and a list of that org's repositories in the main panel with a filter.
   This is what GitHub Actions, Vercel, and Netlify do.
   It scales best and gives the "grant the app access to this org" action an obvious home next to the org it belongs to.

   The trade-off is a second step before the user sees any repos,
   and a lot of empty chrome for someone with one account and five repos,
   which describes most new users.
   It also needs the organization API wired into the page, which the list option doesn't.

Accept a pasted URL
   Let the search input take a repository URL as well as a name.
   If it matches a remote repository, go straight to Continue.
   If not, fall through to the manual form with the URL filled in.
   This is a small addition to any of the above rather than an alternative,
   and it's the fastest path for the user who clicked over from GitHub.
   It needs one new filter on the API.

Fitting the dashboard
---------------------

The dashboard already has one answer to "here are some things, pick one": the list page.
Versions, builds, domains, integrations, webhooks, and about twenty-five other pages all extend the same list template.
Each has the filter form in the top-left menu, a primary button top-right,
a placeholder segment when empty,
and a row per item with an icon, a header, small labels for state, and a button group on the right.
Users learn this shape on their first project and see it everywhere.

The Fomantic UI search dropdown is used on three pages beyond the site-wide header search,
and on this page it is the whole page.
Everywhere else in the dashboard a search dropdown means "jump somewhere", not "choose between these".
That mismatch is most of why the page feels off.

The list option is the one that turns this page into the common shape.
The filter input is the same component every list already has,
the state labels are the same ones the versions list uses for default, stable, and hidden,
and the empty placeholder is the same one every list shows when there's nothing to display.
The grouped option reuses the vertical menu that is already the sidebar on this page for the automatic and manual tabs,
so it fits too, but it introduces a two-panel layout no other dashboard page has.
The hero-search option keeps the odd component and makes it larger.

Recommendation
--------------

Build the list with a filter, and add URL paste to its filter input in a follow-up.
It solves all three parts of the problem, it's the shape users already know,
and it costs about the same as the grouped layout without the empty chrome for small accounts.
Keep the manual import path as a link under the list rather than a sidebar tab,
since the sidebar no longer has a second job.

Hold the grouped layout in reserve.
If large organizations still struggle after the list ships,
the sidebar of organizations can be added on top of the list without redoing it.

Open questions
--------------

- Should the list show every connected account's repos mixed together,
  or default to one account with a dropdown to switch?
- Does anything in the commercial repo override blocks in the import templates?
