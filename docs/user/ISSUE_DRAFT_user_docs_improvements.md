# Docs: high-impact incremental improvements to user documentation

## Summary

The user documentation has good bones — Diátaxis structure, broad feature coverage, a working tutorial — but several of the highest-leverage pages (landing page, Addons, tutorial, FAQ) are leaking value today. At the same time, some of the content I initially considered adding to `docs/` **already lives on the marketing site** ([readthedocs/website](https://github.com/readthedocs/website/)) and should be linked to rather than duplicated — and the website has its own gaps that matter for our value-prop story.

This issue proposes a set of **small, independently-shippable** improvements across both `docs/` and `website/`, each scoped so it can be handed to a contributor or an AI agent as a self-contained PR brief.

## Division of labor: docs vs website

To keep things from duplicating:

| Type of content | Lives in |
| --- | --- |
| Tutorials, how-tos, reference, config | `readthedocs/readthedocs.org` (`docs/`) |
| Value prop, pricing, choosing, competitor comparisons, tool marketing pages, reader feature tour | `readthedocs/website` |

The docs landing page should **link outward** to the website for evaluation content, and the website should link inward to the docs for tutorials and reference. Today both sides under-link to each other.

## What already exists on the website (do not duplicate in docs)

From [`readthedocs/website/content/pages/`](https://github.com/readthedocs/website/tree/main/content/pages):

- [`comparisons/github-pages.html`](https://github.com/readthedocs/website/blob/main/content/pages/comparisons/github-pages.html)
- [`comparisons/gitbook.html`](https://github.com/readthedocs/website/blob/main/content/pages/comparisons/gitbook.html)
- [`comparisons/cloudflare-pages.html`](https://github.com/readthedocs/website/blob/main/content/pages/comparisons/cloudflare-pages.html)
- [`comparisons/netlify.html`](https://github.com/readthedocs/website/blob/main/content/pages/comparisons/netlify.html)
- [`comparisons/index.html`](https://github.com/readthedocs/website/blob/main/content/pages/comparisons/index.html)
- [`features.html`](https://github.com/readthedocs/website/blob/main/content/pages/features.html) (maintainer-facing feature tour)
- [`features/reader.html`](https://github.com/readthedocs/website/blob/main/content/pages/features/reader.html) (reader-facing feature tour — flyout, search-as-you-type, notifications, offline formats)
- [`choosing-a-platform.rst`](https://github.com/readthedocs/website/blob/main/content/pages/choosing-a-platform.rst) (Community vs Business)
- [`tools/sphinx.html`](https://github.com/readthedocs/website/blob/main/content/pages/tools/sphinx.html), [`tools/mkdocs.html`](https://github.com/readthedocs/website/blob/main/content/pages/tools/mkdocs.html), [`tools/jupyter-book.html`](https://github.com/readthedocs/website/blob/main/content/pages/tools/jupyter-book.html), [`tools/markdoc.html`](https://github.com/readthedocs/website/blob/main/content/pages/tools/markdoc.html)
- [`pricing.html`](https://github.com/readthedocs/website/blob/main/content/pages/pricing.html), [`enterprise.html`](https://github.com/readthedocs/website/blob/main/content/pages/enterprise.html), [`docs-as-code.html`](https://github.com/readthedocs/website/blob/main/content/pages/docs-as-code.html), [`homepage.html`](https://github.com/readthedocs/website/blob/main/content/pages/homepage.html)

This means an earlier draft of this plan that proposed new "migration guides" and a new "reader-centric feature tour" inside `docs/` was wrong — **those already exist on the website** and should be linked to instead.

## Context & prior art

- readthedocs/readthedocs.org#10252 Docs: Main page next steps *(closed; visual/prioritization follow-up never fully shipped — this issue is the successor)*
- readthedocs/readthedocs.org#9747 Diátaxis refactor iteration 2 *(closed; `explanation/index.rst` still marked `:orphan:`, and "Choosing a dedicated documentation platform" was checked off by creation of `choosing-a-platform.rst` on the website)*
- readthedocs/readthedocs.org#9746 Diátaxis refactor iteration 1 *(closed)*
- readthedocs/readthedocs.org#9702 Diátaxis task bucket *(closed)*
- readthedocs/readthedocs.org#8329 Getting started with Read the Docs *(closed; predates addons + agent skills + 9 supported tools)*
- readthedocs/readthedocs.org#9938 Translate introductory content *(closed)*

## Diagnosis (what's leaking value)

### In `docs/`

1. **`index.rst` is a table of contents, not a landing page.** 8 toctree captions + duplicated prose link-lists; the real value prop is buried below the `toctree`, and the landing page doesn't link to the website's `features/`, `comparisons/`, or `choosing-a-platform` pages at all.
2. **The tutorial is Sphinx-only.** `intro/doctools.rst` advertises 9 tools; `tutorial/index.rst` (607 lines) walks only Sphinx + `lumache.py`. Non-Sphinx visitors fall off.
3. **Addons — our biggest differentiator — are under-sold and under-linked.** `addons.rst` lives under "Project setup and configuration," is a flat bullet list, and is followed by ~250 lines of CSS-variable + event-data reference a first-time reader doesn't need. It also doesn't link to the website's reader feature tour.
4. **Diátaxis is half-applied.** `explanation/index.rst` is marked `:orphan:` ("unnecessary as a navigation section for now"). Top-level pages (`versions.rst`, `pull-requests.rst`, `custom-domains.rst`, `subprojects.rst`) still mix explanation + how-to + reference.
5. **`intro/add-project.rst` is a dry click-list** with no screenshots — yet it's where every logged-in user lands.
6. **FAQ is stale** — mentions Disqus / `sphinxcontrib-disqus`, recommends `sphinx-rtd-theme` as "the Read the Docs theme," no entries for GitHub App / PR preview privacy / uv / Poetry.
7. **No "preview your build locally" how-to** in one findable place.
8. **`intro/doctools.rst` and the tool-marketing pages on the website duplicate each other** in an unstructured way. The docs version should be scoped to *build configuration per tool*; the website version is the marketing page.

### On `website/`

1. **`features.html` is maintainer-facing but text-only** — no visual showcase of our most differentiated features. It doesn't mention **Addons**, **visual diff**, or **SSO**, and barely mentions analytics.
2. **No dedicated feature pages for our biggest differentiators.** `features/` only contains `reader.html`. There is no page for:
   - Addons (the umbrella brand)
   - Pull request previews + visual diff
   - Versioned documentation with the flyout
   - Server-side search + search analytics
   - Custom domains + CDN
   - SSO
3. **Missing Vercel comparison.** `comparisons/` has GH Pages, GitBook, Cloudflare Pages, Netlify — but Vercel is the most commonly-cited alternative in the current ecosystem and isn't covered.
4. **Missing tool marketing pages** for Docusaurus, VitePress, mdBook, Antora, MyST Markdown, Zensical, while `docs/intro/doctools.rst` advertises all of them as supported.
5. **Homepage CTA set is thin.** Only `/features/` + three `/tools/*` CTAs; doesn't surface `/features/reader/`, `/comparisons/`, or `/choosing-a-platform/`, each of which is high-intent acquisition content.
6. **No explicit link to `docs.readthedocs.io`'s tutorial as a CTA** from the homepage or features page (evaluators often want to read the tutorial before signing up).

## Proposed work — ranked by ROI

Each item is one PR, independent, with concrete file targets.

### P0 — `docs/` landing page rewrite ⭐ highest ROI
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/index.rst`
- **Goal:** Replace duplicated prose link-lists with a short value prop, a feature grid that leads with Addons, and a three-track "where do I go next" block. Keep all existing `:hidden:` toctrees for left-nav.
- **Acceptance:**
  - Visible above-the-fold fits one screen.
  - Three CTAs: "Start from scratch → Tutorial", "Add existing docs → `intro/add-project`", "Evaluate RTD → https://about.readthedocs.com/features/ and https://about.readthedocs.com/comparisons/".
  - Feature grid with ≥6 cards (PR previews, visual diff, flyout/versions, server-side search, analytics, custom domains/SSO), each linking to the relevant `docs/` page *and* to the website feature page once it exists.
  - No content removed from left nav.
- **Successor to:** readthedocs/readthedocs.org#10252.

### P0 — Addons showcase + reference split ⭐
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/addons.rst` (rewrite top), new `docs/user/reference/addons.rst` (extract reference)
- **Goal:** Top of `addons.rst` becomes a showcase with screenshots/gifs; CSS-variables, custom-event integration, and event-data reference move to `reference/addons.rst`.
- **Acceptance:**
  - `addons.rst` readable in <2 minutes, one screenshot per addon.
  - All reference material moves to `reference/addons.rst` with a stable anchor.
  - Promote `addons.rst` out of the "Project setup and configuration" toctree caption into a top-level "Features" caption in `index.rst`.
  - Cross-links to https://about.readthedocs.com/features/reader/ where relevant.

### P0 — `website/`: maintainer-facing Addons / PR-preview / versioning feature pages ⭐
- **Repo:** `readthedocs/website`
- **Files:** new `content/pages/features/addons.html`, new `content/pages/features/pull-request-previews.html`, new `content/pages/features/versioned-documentation.html`; update `content/pages/features.html` to link to them.
- **Goal:** Build out `features/` to match `features/reader.html` in quality, covering our three most differentiated maintainer-facing capabilities. Each page is one scrollable marketing page with screenshots/gifs, one-line promise, and CTA to sign up.
- **Acceptance:**
  - Each feature page has ≥3 screenshots / gifs.
  - `features.html` hub links to all three new pages + existing `reader.html`.
  - Each page has a "Read the docs" link to the relevant `docs/` page for deep-dive.
  - Homepage CTA updated to surface `features/addons/` or `features/pull-request-previews/` as the third "Explore features" secondary CTA.

### P1 — 5-minute quickstart (tool-agnostic)
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** new `docs/user/intro/quickstart.rst`; link from `index.rst` and `intro/doctools.rst`
- **Goal:** One page, tabbed Sphinx / MkDocs / Docusaurus. Each tab: copy this `.readthedocs.yaml`, push, connect, done.
- **Acceptance:** Fits on one page; each tab references an existing `readthedocs-examples/` repo; linked from landing page and from each tool intro.

### P1 — MkDocs and Docusaurus tutorials (sibling to the Sphinx tutorial)
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** new `docs/user/tutorial/mkdocs.rst`, new `docs/user/tutorial/docusaurus.rst`; turn `docs/user/tutorial/index.rst` into a tool-chooser.
- **Goal:** Reuse Sphinx tutorial structure and screenshots. Use existing example repos.
- **Acceptance:** New-user onboarding works end-to-end without touching Sphinx.

### P1 — `website/`: fill tool marketing page gaps
- **Repo:** `readthedocs/website`
- **Files:** new `content/pages/tools/docusaurus.html`, `tools/vitepress.html`, `tools/mdbook.html`, `tools/antora.html`, `tools/mystmd.html`, `tools/zensical.html`; update `content/pages/tools/index.html` to list them all.
- **Goal:** Match the 9 tools advertised in `docs/user/intro/doctools.rst`. Each page is one marketing page with a CTA into the docs tutorial or quickstart for that tool.
- **Acceptance:** Every tool in `intro/doctools.rst` has a corresponding `tools/*.html`. Homepage CTAs can now rotate or pick-one based on the most relevant tool.

### P1 — `website/`: add Vercel comparison
- **Repo:** `readthedocs/website`
- **Files:** new `content/pages/comparisons/vercel.html`; update `comparisons/index.html`.
- **Goal:** Match the existing four competitor comparisons. Same structure as `netlify.html`.
- **Acceptance:** Page exists, listed on the comparisons hub, and is linked to from `docs/user/index.rst` "Evaluate" CTA alongside the others.

### P2 — `docs/intro/add-project.rst` walk-through with screenshots
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/intro/add-project.rst`
- **Goal:** Add dashboard / GitHub App install / "config file exists" screenshots; add "what success looks like" closing block.
- **Acceptance:** ≥3 new screenshots; explicit "you should now see X" after each step.

### P2 — Diátaxis cleanup round 3
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/explanation/index.rst`, `versions.rst`, `subprojects.rst`, `pull-requests.rst`, `custom-domains.rst`
- **Goal:** Un-orphan (or cleanly delete) `explanation/index.rst`. Push reference sub-sections into `reference/*` and how-to steps into `guides/*`.
- **Acceptance:** No file is `:orphan:` *and* linked from `index.rst`; each touched top-level page is pure explanation, reference, or how-to.
- **Picks up:** leftover items from readthedocs/readthedocs.org#9702 and readthedocs/readthedocs.org#9747.

### P2 — "Preview your build locally" how-to
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** new `docs/user/guides/build/preview-locally.rst`
- **Goal:** Single how-to covering the pinned build image / `rtd-build` workflow.
- **Acceptance:** Copy-paste works on macOS + Linux; linked from `config-file/index.rst`, `build-customization.rst`, and `guides/troubleshooting/index.rst`.

### P2 — `docs/intro/doctools.rst` scope clean-up
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/intro/doctools.rst` and the per-tool `intro/*.rst` pages.
- **Goal:** Re-scope these pages to be **build-config how-to** per tool, not marketing. Each page ends with a prominent "Learn more about \<tool\> on Read the Docs →" link to the matching `about.readthedocs.com/tools/*` page.
- **Acceptance:** The per-tool docs pages contain config snippets and gotchas, not sales copy; the website's `tools/*` pages own the marketing story.

### P3 — FAQ triage
- **Repo:** `readthedocs/readthedocs.org`
- **Files:** `docs/user/faq.rst`
- **Goal:** Remove dead entries (Disqus, `sphinxcontrib-disqus`, `sphinx-rtd-theme` as "the RTD theme"). Add: "Do I need the GitHub App?", "Why is my PR preview on `*.readthedocs.build`?", "How do I use uv / Poetry / PDM?", "How do I make PR previews private?", "How do I migrate from another platform?" (linking out to `about.readthedocs.com/comparisons/`).
- **Acceptance:** Every answer ≤3 sentences, links to a canonical page.

## Explicitly out of scope

- **Platform-migration guides in `docs/`** — these already exist at `about.readthedocs.com/comparisons/*` and should not be duplicated.
- **Reader-centric feature tour in `docs/`** — `about.readthedocs.com/features/reader/` already covers this.
- **"Choosing a dedicated documentation platform" in `docs/`** — `about.readthedocs.com/choosing-a-platform/` already covers this.
- Rewriting `config-file/v2.rst` — it's doing its job as reference.
- Rewriting the existing Sphinx tutorial — we're adding siblings, not replacing.
- Translations — let introductory content stabilize first (cf. readthedocs/readthedocs.org#9938).

## Suggested first PRs

Two parallel PRs that together immediately tighten the value-prop story end-to-end:

1. **`docs/` landing + Addons split + quickstart skeleton** (one PR, ~4 files). Closes the three worst docs leaks.
2. **`website/` `features/addons.html` + `features/pull-request-previews.html`** (one PR, two files). Gives the docs landing page something real to link to for the "Evaluate RTD" CTA.

## Shovel-readiness

Every sub-task above lists: **repo**, **files**, **goal**, and **acceptance criteria**. Any one is a self-contained PR brief for a contributor or AI agent. Items that touch both repos are noted explicitly.
