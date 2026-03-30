Roadmap Prioritization Review (March 2026)
============================================

This document provides a data-driven review of the `Read the Docs Roadmap
<https://github.com/orgs/readthedocs/projects/156/views/15>`_ with
concrete recommendations for improving prioritization.

The analysis is based on reaction counts, comment volume, issue age,
dependency chains, and whether work-in-progress already exists.

Executive summary
-----------------

1. **The roadmap is missing the community's most-requested open issues.**
   The top-voted issues in the repository are absent from the board.
2. **~10 items are blocked on "Needed: design decision"** with no visible
   process to unblock them.
3. **Several items have draft PRs that just need review** -- these are the
   cheapest wins on the board.
4. **Bugs and features are interleaved without priority tiers**, making it
   hard for the team to know what to work on next.

Data-driven issue ranking
-------------------------

The table below ranks every open roadmap item using a composite score:

.. list-table::
   :header-rows: 1
   :widths: 10 45 8 8 8 12 9

   * - Issue
     - Title
     - +1s
     - Comments
     - Age (yr)
     - Status
     - Score
   * - `#6311 <https://github.com/readthedocs/readthedocs.org/issues/6311>`_
     - Allow setting open build env vars in ``.readthedocs.yml``
     - 13
     - 16
     - 6.4
     - Needs design decision
     - **A**
   * - `#5319 <https://github.com/readthedocs/readthedocs.org/issues/5319>`_
     - Add latest/stable rules to version automation
     - 5
     - 26
     - 7.1
     - Accepted, assigned
     - **A**
   * - `#8649 <https://github.com/readthedocs/readthedocs.org/issues/8649>`_
     - HTTP Header: allow on non-custom domains
     - 4
     - 1
     - 4.4
     - Accepted
     - **B+**
   * - `#11001 <https://github.com/readthedocs/readthedocs.org/issues/11001>`_
     - Audit: extend log to cover project actions
     - 1
     - 1
     - 2.2
     - Draft PR #12870
     - **B+**
   * - `#11179 <https://github.com/readthedocs/readthedocs.org/issues/11179>`_
     - API v3: BuildCommands and missing fields
     - 0
     - 3
     - 2.1
     - In progress, PR #12794
     - **B+**
   * - `#11365 <https://github.com/readthedocs/readthedocs.org/issues/11365>`_
     - GitLab: trigger builds for MR on code changes only
     - 0
     - 1
     - 1.8
     - Accepted bug
     - **B**
   * - `#11339 <https://github.com/readthedocs/readthedocs.org/issues/11339>`_
     - Version: queryset ordered backwards
     - 0
     - --
     - 1.9
     - Bug, draft PR #12636
     - **B**
   * - `#11387 <https://github.com/readthedocs/readthedocs.org/issues/11387>`_
     - Project language locales out of date
     - 0
     - 4
     - 1.8
     - Accepted bug
     - **B**
   * - `#10886 <https://github.com/readthedocs/readthedocs.org/issues/10886>`_
     - PR previews: allow building from project members only
     - 0
     - 8
     - 2.4
     - Needs design decision
     - **B**
   * - `#11978 <https://github.com/readthedocs/readthedocs.org/issues/11978>`_
     - Redirects: suggest redirect when changing version slug
     - 0
     - 5
     - 1.2
     - Open
     - **B-**
   * - `#11864 <https://github.com/readthedocs/readthedocs.org/issues/11864>`_
     - Build: store build job in BuildCommand
     - 0
     - 0
     - 1.3
     - Blocked on #11179
     - **C+**
   * - `#6841 <https://github.com/readthedocs/readthedocs.org/issues/6841>`_
     - Link to subprojects from sitemap.xml
     - 1
     - 5
     - 6.0
     - 2 open PRs, no merge
     - **C+**
   * - `#11979 <https://github.com/readthedocs/readthedocs.org/issues/11979>`_
     - Version: introduce display_name field
     - 0
     - 0
     - 1.2
     - Needs design decision
     - **C**
   * - `#11970 <https://github.com/readthedocs/readthedocs.org/issues/11970>`_
     - API v3: allow changing the version slug
     - 0
     - 0
     - 1.2
     - Accepted, behind feature flag
     - **C**
   * - `#7005 <https://github.com/readthedocs/readthedocs.org/issues/7005>`_
     - Add debug flag to build commands
     - 0
     - 26
     - 5.9
     - Accepted
     - **C**
   * - `#11182 <https://github.com/readthedocs/readthedocs.org/issues/11182>`_
     - Addons: use verbose_name instead of slug
     - 0
     - 0
     - 2.1
     - Accepted
     - **C**
   * - `#8141 <https://github.com/readthedocs/readthedocs.org/issues/8141>`_
     - Default email notifications on, warn when disabled
     - 0
     - 6
     - 4.9
     - Needs design decision
     - **C-**
   * - `#9365 <https://github.com/readthedocs/readthedocs.org/issues/9365>`_
     - Submodules: user message when problems cloning
     - 0
     - 1
     - 3.8
     - Accepted
     - **C-**
   * - `#12127 <https://github.com/readthedocs/readthedocs.org/issues/12127>`_
     - Update docs with new dashboard UI
     - 1
     - 4
     - 0.9
     - Accepted, assigned
     - **C-**

*Scoring: A = high community demand + actionable. B = clear value + near-ready
or bug. C = lower signal or blocked. Within tiers, items with existing PRs rank
higher.*

Recommendation 1: Add high-demand community issues to the roadmap
-----------------------------------------------------------------

The following issues have **strong community signal** (reactions + comments)
but are **not on the roadmap board**:

.. list-table::
   :header-rows: 1
   :widths: 10 50 8 8 24

   * - Issue
     - Title
     - +1s
     - Comments
     - Why it matters
   * - `#1083 <https://github.com/readthedocs/readthedocs.org/issues/1083>`_
     - Upload pre-built docs
     - **24**
     - 40
     - Most-upvoted open issue in the entire repo. 12 years old.
       Either commit to it or close it with a clear rationale.
   * - `#10021 <https://github.com/readthedocs/readthedocs.org/issues/10021>`_
     - Support GitHub merge queues
     - **11**
     - 20
     - Merge queues are now mainstream. Projects using required
       RTD checks cannot adopt them.
   * - `#11289 <https://github.com/readthedocs/readthedocs.org/issues/11289>`_
     - Support uv
     - **3**
     - 34
     - ``uv`` adoption is accelerating rapidly. High comment
       volume signals active demand.
   * - `#5208 <https://github.com/readthedocs/readthedocs.org/issues/5208>`_
     - Structured metadata for search & SEO
     - **5**
     - 10
     - Directly impacts discoverability of hosted docs.
   * - `#11220 <https://github.com/readthedocs/readthedocs.org/issues/11220>`_
     - Redirects: clean file URLs as well
     - **5**
     - 19
     - Active discussion, high engagement.

These represent real user pain points that the roadmap does not currently
reflect.

Recommendation 2: Unblock "Needed: design decision" items
----------------------------------------------------------

Ten roadmap items carry the ``Needed: design decision`` label. Some have
been in this state for **years**:

- **#6311** -- 6.4 years (13 thumbs-up!)
- **#8141** -- 4.9 years
- **#10886** -- 2.4 years
- **#11001** -- 2.2 years (has a draft PR waiting)

**Proposed process:**

1. Schedule a monthly 1-hour "design decision" session focused exclusively
   on these items.
2. For each item, timebox to 15 minutes: either make the decision, mark it
   as "won't do", or document what information is still missing.
3. After a decision is made, immediately remove the label so the item
   becomes actionable.

Recommendation 3: Ship the "almost done" items first
-----------------------------------------------------

Three roadmap items already have draft PRs. These represent the highest
ROI because most of the implementation work is complete:

1. **#11001** (Audit log) -- draft PR `#12870
   <https://github.com/readthedocs/readthedocs.org/pull/12870>`_.
   Real-world user story (CherryPy project deleted without trace).
2. **#11339** (Version queryset ordering bug) -- draft PR `#12636
   <https://github.com/readthedocs/readthedocs.org/pull/12636>`_.
   A correctness bug visible in the dashboard.
3. **#11179** (API v3 BuildCommands) -- PR `#12794
   <https://github.com/readthedocs/readthedocs.org/pull/12794>`_ open.
   Blocks #11864 (store build job in BuildCommand) which in turn blocks
   build detail page improvements.

Finishing these three items would close 3 issues, unblock at least 2 more
downstream issues, and demonstrate momentum on the roadmap.

Recommendation 4: Create explicit priority tiers
-------------------------------------------------

The roadmap currently has no visible priority ordering within categories.
A simple tier system would help:

**Tier 1 -- Do next** (bugs, security, high demand, or near-complete):

- #11365 -- GitLab MR build trigger bug (accepted bug, clear fix)
- #11339 -- Version ordering bug (draft PR exists)
- #11001 -- Audit log (draft PR exists, security-adjacent)
- #11179 -- API v3 BuildCommands (in progress, unblocks #11864)
- #6311 -- YAML env vars (13 thumbs-up, most-upvoted roadmap item)

**Tier 2 -- Do soon** (clear value, design decided or nearly decided):

- #10886 -- PR previews member-only (security feature)
- #8649 -- HTTP headers on non-custom domains (4 thumbs-up)
- #5319 -- Version automation rules (5 thumbs-up, 26 comments)
- #11978 -- Redirect suggestion on slug change (prevents user 404s)
- #12127 -- Update docs for new dashboard UI

**Tier 3 -- Backlog** (needs design work or low signal):

- #11979 -- Version display_name field
- #11970 -- API v3 version slug change
- #7005 -- Debug flag for build commands
- #6841 -- Subproject sitemaps (6 years, 2 stalled PRs)
- #8141 -- Default email notifications (5 years, no movement)
- #9365 -- Submodule error messages
- #11182 -- Addons verbose_name

Recommendation 5: Recognize dependency chains
----------------------------------------------

Several items form chains that should be worked on in order:

**Chain A -- Version management:**

::

    #11979 (display_name field)
      --> #11182 (addons: use verbose_name)
      --> #11970 (API v3 slug change)
      --> #11978 (redirect on slug change)

These should be sequenced together in a single epic rather than
scattered across categories.

**Chain B -- Build detail page:**

::

    #11179 (API v3 BuildCommands)     <-- IN PROGRESS
      --> #11864 (store build job in BuildCommand)
        --> ext-theme#171 (build detail page improvements)
          --> #7005 (debug flag for build commands)

#11179 is the critical path. Everything downstream is blocked until it
ships.

Recommendation 6: Triage or close stale items
----------------------------------------------

Items that have been open for 4+ years with no recent progress should
be explicitly triaged:

- **#8141** (default email notifications) -- 4.9 years, last comment
  Sept 2023. If no design decision has been made in 5 years, either
  make a quick decision or close it.
- **#6841** (subproject sitemaps) -- 6 years, 2 open PRs neither
  merged. Decide: merge one, or close the issue.
- **#7005** (debug flag for builds) -- 5.9 years. 26 comments suggest
  ongoing interest, but it may be waiting on Chain B above.
- **#9365** (submodule error messages) -- 3.8 years, 1 comment.
  Low activity suggests low actual priority despite being "Accepted".

Recommendation 7: Track AI/docs trends
---------------------------------------

The recent completion of **#12512** (content negotiation for AI agents)
shows awareness of the AI-docs trend. Consider adding follow-up items:

- ``llms.txt`` support (emerging standard for AI-friendly docs)
- Analytics for AI crawler traffic patterns
- Structured API endpoints for documentation content
- MCP server support for documentation retrieval

These could differentiate Read the Docs in an increasingly AI-driven
documentation consumption landscape.
