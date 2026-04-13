# Docs: high-impact incremental improvements to user documentation

## Summary

The user documentation has good bones — Diátaxis structure, broad feature coverage, a working tutorial — but several of the highest-leverage pages (landing page, Addons, tutorial, examples, FAQ) are leaking value today. This issue proposes a set of **small, independently-shippable** improvements that together meaningfully move the "first-time visitor → activated project" and "evaluator → believer" funnels.

Each sub-task below is scoped to be a single PR, with concrete file targets and acceptance criteria, so it can be picked up directly by a teammate or an AI agent without further planning.

## Context & prior art

This builds on (and picks up some leftover threads from) earlier docs work:

- #10252 Docs: Main page next steps *(closed; the visual/prioritization follow-up was never fully done — this issue is its natural successor)*
- #9747 Diátaxis refactor iteration 2 *(closed; the "Explanation" section still ended up marked `:orphan:`, and "New article: Choosing a dedicated documentation platform" was left unchecked)*
- #9746 Diátaxis refactor iteration 1 *(closed)*
- #9702 Diátaxis task bucket *(closed)*
- #8329 Getting started with Read the Docs *(closed; predates addons + agent skills + 9 supported tools)*
- #9938 Translate introductory content *(closed; our introductory content has since expanded and drifted)*

## Diagnosis (what's leaking value)

1. **`index.rst` is a table of contents, not a landing page.** 8 captions + duplicated prose link-lists; the actual value prop is buried below the `toctree`.
2. **The tutorial is Sphinx-only.** `intro/doctools.rst` advertises 9 tools; `tutorial/index.rst` (607 lines) walks only Sphinx + `lumache.py`. Every non-Sphinx visitor falls off here.
3. **Addons — our biggest differentiator — are under-sold.** `addons.rst` lives under "Project setup and configuration," is a flat bullet list, and is followed by ~250 lines of CSS-variable + event-data reference that a first-time reader doesn't need.
4. **Diátaxis is half-applied.** `explanation/index.rst` is marked `:orphan:` ("unnecessary as a navigation section for now"). Top-level pages (`versions.rst`, `pull-requests.rst`, `custom-domains.rst`, `subprojects.rst`) still mix explanation + how-to + reference.
5. **`examples.rst` is a stub** (86 lines, 4 examples, mostly about how to contribute examples).
6. **`intro/add-project.rst` is a dry click-list** with no screenshots or "what success looks like" — yet it's where every logged-in user lands after signup.
7. **FAQ is stale** — mentions Disqus / `sphinxcontrib-disqus`, recommends `sphinx-rtd-theme` as "the Read the Docs theme," no entries for GitHub App / PR preview privacy / uv / Poetry / migrating from other platforms.
8. **No platform-migration guides** (GitHub Pages, Netlify, Vercel, Cloudflare Pages) — the single highest-intent acquisition page category we don't cover.
9. **No reader-centric page.** Everything is written for maintainers; there's no one-page "here's what your readers get" that a maintainer can use to sell RTD internally.
10. **No "preview your build locally" how-to** in one findable place.

## Proposed work — ranked by ROI

Each item below is one PR. They are independent; ship them in any order.

### P0 — Landing page rewrite ⭐ highest ROI
**Files:** `docs/user/index.rst`
**Goal:** Replace the duplicated prose link-lists with a short value prop, a feature grid that leads with Addons, and a three-track "where do I go next" block. Keep all existing `:hidden:` toctrees for left-nav.
**Acceptance:**
- Visible above-the-fold content fits one screen.
- Three CTAs: "Start from scratch → Tutorial", "Add existing docs → `intro/add-project`", "Evaluate RTD → new Features tour".
- Feature grid with ≥6 cards (PR previews, visual diff, flyout/versions, server-side search, analytics, custom domains/SSO), each linking to its page.
- No content removed from left nav.
**Successor to:** #10252.

### P0 — Addons showcase + reference split ⭐
**Files:** `docs/user/addons.rst` (rewrite top), new `docs/user/reference/addons.rst` (extract reference)
**Goal:** Top of `addons.rst` becomes a showcase with screenshots/gifs; CSS-variables reference, custom-event integration, and event-data reference move to `reference/addons.rst`.
**Acceptance:**
- `addons.rst` is readable in <2 minutes and contains at least one screenshot per addon.
- All reference material (CSS vars, events, JSON payload) moves to `reference/addons.rst` with a stable anchor.
- Promote `addons.rst` out of the "Project setup and configuration" toctree caption and into a new top-level "Features" caption (or the "Hosting documentation" caption) in `index.rst`.

### P1 — 5-minute quickstart (tool-agnostic)
**Files:** new `docs/user/intro/quickstart.rst`; link from `index.rst` and `intro/doctools.rst`
**Goal:** One page, tabbed Sphinx / MkDocs / Docusaurus. Each tab: copy this `.readthedocs.yaml`, push, connect repo, done. Screenshot of the resulting dashboard.
**Acceptance:**
- Fits on one page.
- Each tab references an existing working example repo under `readthedocs-examples/`.
- Linked from the landing page's "Start from scratch" CTA *and* from each tool intro page.

### P1 — MkDocs and Docusaurus tutorials (sibling to the Sphinx tutorial)
**Files:** new `docs/user/tutorial/mkdocs.rst`, new `docs/user/tutorial/docusaurus.rst`; update `docs/user/tutorial/index.rst` to be a tool-chooser landing page that points at the three siblings.
**Goal:** Reuse the Sphinx tutorial structure and screenshots where possible. Each tutorial uses an existing `readthedocs-examples/*` template repo.
**Acceptance:**
- New-user onboarding works end-to-end without touching Sphinx.
- Tutorial index page routes users by tool.
- Closes the known gap from #8329 that predated non-Sphinx tools being first-class.

### P1 — Reader-centric feature tour
**Files:** new `docs/user/explanation/what-readers-get.rst` (or top-level `features-for-readers.rst`)
**Goal:** One-page marketing-quality tour of what end-users of docs see: flyout, search-as-you-type, link previews, PR preview banner, non-stable notification, visual diff, analytics opt-out. Written for a maintainer to skim and use to convince teammates.
**Acceptance:**
- Each feature gets one sentence + one screenshot/gif.
- Linked prominently from `index.rst` as the "Evaluate RTD" CTA.
- Also fulfills the unchecked "Choosing a dedicated documentation platform" item from #9747.

### P1 — Platform-migration guides
**Files:**
- `docs/user/guides/migrate/from-github-pages.rst`
- `docs/user/guides/migrate/from-netlify.rst`
- `docs/user/guides/migrate/from-vercel.rst`
- `docs/user/guides/migrate/from-cloudflare-pages.rst`
- Hub: `docs/user/guides/migrate/index.rst`
**Goal:** For each platform: equivalent `.readthedocs.yaml`, what you gain (link to Addons showcase and reader-tour), custom-domain cutover, redirects story.
**Acceptance:**
- Each page is self-contained (~1 page).
- Each page has an SEO-optimized H1 and a meta description.
- Linked from the landing page and from a new "Migrate to Read the Docs" section in the how-to hub.

### P2 — `intro/add-project.rst` walk-through with screenshots
**Files:** `docs/user/intro/add-project.rst`
**Goal:** Add inline screenshots of the dashboard, GitHub App install flow, and the "config file exists" step. Add a "what success looks like" closing block.
**Acceptance:**
- ≥3 new screenshots.
- Explicit "you should now see X" statements after each step.

### P2 — Diátaxis cleanup round 3
**Files:** `docs/user/explanation/index.rst`, `docs/user/versions.rst`, `docs/user/subprojects.rst`, `docs/user/pull-requests.rst`, `docs/user/custom-domains.rst`
**Goal:** Un-orphan `explanation/index.rst` (or delete it cleanly — don't leave it in half-state). Push reference sub-sections into `reference/*` and how-to steps into `guides/*`, leaving each top-level page as a clean explanation hub.
**Acceptance:**
- No file in the tree is marked `:orphan:` *and* linked from `index.rst`.
- Each touched top-level page is one of: pure explanation, pure reference, pure how-to — not all three.
**Picks up:** leftover items from #9702 and #9747.

### P2 — `examples.rst` rewrite
**Files:** `docs/user/examples.rst`
**Goal:** Inline a minimum `.readthedocs.yaml` for each example so readers can copy it without leaving the page. One example per supported tool. "Contribute a new example" block moves to the bottom.
**Acceptance:**
- One example per tool listed in `intro/doctools.rst`.
- Copy-pasteable `.readthedocs.yaml` inline for each.

### P2 — "Preview your build locally" how-to
**Files:** new `docs/user/guides/build/preview-locally.rst`
**Goal:** Single how-to covering the pinned build image / `rtd-build` style workflow, so users can iterate on `.readthedocs.yaml` without pushing commits.
**Acceptance:**
- Works copy-paste on macOS and Linux.
- Linked from `config-file/index.rst`, `build-customization.rst`, and `guides/troubleshooting/index.rst`.

### P3 — FAQ triage
**Files:** `docs/user/faq.rst`
**Goal:** Remove dead entries (Disqus, `sphinxcontrib-disqus`, "use the sphinx-rtd-theme"). Add entries for: "Do I need the GitHub App?", "Why is my PR preview on `*.readthedocs.build`?", "How do I use uv / Poetry / PDM?", "How do I make PR previews private?", "How do I migrate from \<platform\>?".
**Acceptance:**
- No entries older than the `.readthedocs.yaml` era remain un-updated.
- Every answer is ≤3 sentences and links to a canonical page.

## Explicitly out of scope

- Rewriting `config-file/v2.rst` (it's doing its job as reference).
- Rewriting the existing Sphinx tutorial (we're adding siblings, not replacing it).
- Theme / visual design changes.
- API reference rewrite — `reference/agent-skills.rst` is already a modern on-ramp for programmatic use.
- Translations — let introductory content stabilize first (cf. #9938).

## Suggested first PR

P0 + P0 combined: rewrite `index.rst`, split Addons into showcase + reference, and add a skeleton `intro/quickstart.rst`. ~4 files touched, content-only, immediately fixes the three worst leaks (buried value prop, buried differentiators, Sphinx-only onramp).

## Shovel-readiness checklist

Each sub-task above lists: **files to touch**, **goal**, **acceptance criteria**, and where applicable, **prior-art issue links**. Any of them can be handed to a contributor or an AI agent as a self-contained PR brief.
