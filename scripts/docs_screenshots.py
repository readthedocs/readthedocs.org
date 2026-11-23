# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright"]
# ///
"""
Regenerate the dashboard screenshots used in the user documentation.

Each screenshot is a function registered with ``@shot``. It opens a page on the
local development instance, tidies it up for publishing, and returns the area to
capture. Images are written straight into ``docs/user/``, so ``git diff`` shows
what changed.

Conventions, sample data rules, and how to add a new screenshot are documented
in ``docs/dev/screenshots.rst``. Read it before changing this script.

Usage::

    export RTD_COMMUNITY_SESSIONID=...   # sessionid cookie from devthedocs.org
    export RTD_BUSINESS_SESSIONID=...    # sessionid cookie from devthedocs.com
    uv run scripts/docs_screenshots.py --list
    uv run scripts/docs_screenshots.py                    # all of them
    uv run scripts/docs_screenshots.py redirects tutorial  # names containing any filter

Only one development instance (Community or Business) runs at a time.
Shots for the instance that isn't running are skipped with a warning.
"""

import argparse
import base64
import json
import math
import os
import random
import sys
from pathlib import Path

from playwright.sync_api import Error
from playwright.sync_api import sync_playwright


COMMUNITY_URL = os.environ.get("RTD_COMMUNITY_URL", "http://devthedocs.org")
BUSINESS_URL = os.environ.get("RTD_BUSINESS_URL", "http://devthedocs.com")
SESSIONS = {
    "community": os.environ.get("RTD_COMMUNITY_SESSIONID"),
    "business": os.environ.get("RTD_BUSINESS_SESSIONID"),
}
DOCS_USER = Path(__file__).resolve().parents[1] / "docs" / "user"

# Objects from the development database that screenshots borrow.
# These depend on your local data: update them if your database is different.
# See "Data sources" in docs/dev/screenshots.rst for what each one needs.
SOURCES = {
    # Community project with exactly two versions: ``latest`` and ``stable``.
    "project": "docs",
    # Community project with redirects, analytics data, an integration with
    # webhook calls, and a successful standard Sphinx build.
    "busy_project": "test-builds",
    "busy_integration": 1,
    "busy_build": 5800,
    # Community project with an outgoing webhook, and one with a subproject.
    "webhook_project": "pycampes",
    "webhook": 1,
    "subproject_parent": "website",
    # Business: team to highlight in "Add project", and a project with an SSH key.
    "business_team": "13-30",
    "business_ssh_project": "admin-test-builds-git-ssh",
    "business_ssh_key": 116,
    # Public docs built from the tutorial template, captured for "first light".
    "tutorial_live_docs": "https://readthedocs-tutorial.readthedocs.io/en/latest/",
}

# Names shown in the screenshots. Never publish real usernames or projects.
PROJECT = "docs"
TUTORIAL_PROJECT = "tutorial"
TUTORIAL_REPO = "https://github.com/example-user/tutorial"
TUTORIAL_URL = "https://tutorial.readthedocs.io/en/latest/"
USERNAME = "example-user"
ORGANIZATIONS = ["Example Docs", "Example Company"]
AVATAR = "https://assets.readthedocs.org/static/images/silhouette.png"
HIGHLIGHT = "#2185d0"
# Python versions the tutorial talks about: the template default and the latest.
TUTORIAL_PYTHON_TEMPLATE = "3.13.14"

WIDTH = 1280
PAD = 16
# Left/right edges of the dashboard page container at WIDTH.
CONTAINER_X = (80, 1200)

SHOTS = []


def shot(path, instance="community", scale=1):
    """Register a screenshot written to ``docs/user/<path>``."""

    def register(func):
        SHOTS.append({"path": path, "func": func, "instance": instance, "scale": scale})
        return func

    return register


def base(instance):
    return COMMUNITY_URL if instance == "community" else BUSINESS_URL


# Applied to every dashboard page before capturing.
TIDY_JS = """
([avatar, busyProject, project]) => {
  document.documentElement.dataset.theme = 'light';
  for (const img of document.querySelectorAll('img[src*="gravatar.com"]')) img.src = avatar;
  const style = document.createElement('style');
  style.textContent = 'readthedocs-notification { display: none !important; } #djDebug { display: none !important; }';
  document.head.append(style);
  // Organization and "Unofficial" badges in the project header, and the staff-only Debug tab
  for (const el of document.querySelectorAll('a.ui.label[href*="/organizations/"]')) el.remove();
  for (const el of document.querySelectorAll('.ui.label, a.item')) {
    if (['Unofficial', 'Debug'].includes(el.textContent.trim())) el.remove();
  }
  const help = [...document.querySelectorAll('h2')].find(h => h.textContent.trim() === 'Help topics');
  help?.closest('.segment')?.remove();
  for (const el of document.querySelectorAll('input')) {
    el.value = el.value.replace(/https?:\\/\\/devthedocs\\.(org|com)/g, 'https://app.readthedocs.org');
  }
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.nodeValue.includes(busyProject)) node.nodeValue = node.nodeValue.replaceAll(busyProject, project);
  }
}
"""


def tidy(page):
    page.evaluate(TIDY_JS, [AVATAR, SOURCES["busy_project"], PROJECT])


def goto(page, url):
    page.goto(url, wait_until="networkidle")
    tidy(page)


def replace_text(page, pairs, regex=False):
    """Replace text in text nodes and form values."""
    page.evaluate(
        """([pairs, regex]) => {
          const swap = s => pairs.reduce(
            (acc, [a, b]) => regex ? acc.replace(new RegExp(a, 'g'), b) : acc.replaceAll(a, b), s);
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) walker.currentNode.nodeValue = swap(walker.currentNode.nodeValue);
          for (const el of document.querySelectorAll('input, textarea')) el.value = swap(el.value);
        }""",
        [pairs, regex],
    )


def recent_times(page, when="2 minutes ago"):
    """Make relative times like "1 year, 3 months ago" look recent."""
    replace_text(
        page,
        [[r"\b(a|an|\d+)\s+(year|month|week|day|hour)s?(,\s*\d+\s+\w+)?\s+ago\b", when]],
        regex=True,
    )


def set_counters(page, versions, builds):
    """Set the Versions/Builds counters in the project header."""
    page.evaluate(
        """([versions, builds]) => {
          for (const item of document.querySelectorAll('a.item')) {
            const label = item.querySelector('.label');
            if (!label) continue;
            if (item.textContent.trim().startsWith('Versions')) label.textContent = versions;
            if (item.textContent.trim().startsWith('Builds')) label.textContent = builds;
          }
        }""",
        [str(versions), str(builds)],
    )


def daily_series(average, seed):
    """31 days of plausible numbers: weekday highs, weekend dips, some noise."""
    rng = random.Random(seed)
    values = []
    for day in range(31):
        weekend = day % 7 in (5, 6)
        trend = 1 + 0.15 * math.sin(day / 31 * math.pi)
        values.append(round(average * trend * rng.uniform(0.85, 1.15) * (0.45 if weekend else 1)))
    return values


def chart_data(page, values):
    """
    Replace the data of the analytics chart before Knockout reads it.

    Don't rewrite the HTML response with ``page.route``: Chrome then treats the
    page as public and blocks the local CSS/JS (private network access checks).
    """
    page.add_init_script(
        """
        document.addEventListener('readystatechange', () => {
          if (document.readyState !== 'interactive') return;
          for (const script of document.querySelectorAll('script[type="application/json"]')) {
            try {
              const config = JSON.parse(script.textContent);
              if (config.type !== 'line') continue;
              config.data.datasets[0].data = VALUES;
              script.textContent = JSON.stringify(config);
            } catch (e) {}
          }
        }, {capture: true});
        """.replace("VALUES", json.dumps(values))
    )


def fake_api(page, pattern, data):
    """Answer an API call with sample data (fine for XHR, not for the page itself)."""
    page.route(
        pattern,
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps(data)
        ),
    )


def box(page, selector):
    return page.locator(selector).first.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          return {top: r.top + window.scrollY, bottom: r.bottom + window.scrollY, left: r.left, right: r.right};
        }"""
    )


# --- Clip helpers: what part of the page to capture ---------------------------


def above_footer(page):
    """The whole page, without the footer."""
    bottom = page.evaluate(
        "document.querySelector('footer, .footer').getBoundingClientRect().top + window.scrollY"
    )
    return {"x": 0, "y": 0, "width": WIDTH, "height": bottom}


def content_column(page, top_selector, bottom_selector):
    """The right-hand content column, between two elements."""
    top = box(page, top_selector)
    bottom = box(page, bottom_selector)
    return {
        "x": top["left"] - PAD,
        "y": top["top"] - PAD,
        "width": CONTAINER_X[1] - top["left"] + 2 * PAD,
        "height": bottom["bottom"] - top["top"] + 2 * PAD,
    }


def main_column(page):
    """The main content column: from its heading to the end of its content."""
    b = page.evaluate(
        """() => {
          // The content column is the one with a heading and without the sidebar menu
          const heading = [...document.querySelectorAll('h2')].find(h => {
            const column = h.closest('.column');
            return column && !column.querySelector('.ui.vertical.menu') && h.offsetHeight;
          });
          const column = heading.closest('.column');
          const rects = [...column.children].map(c => c.getBoundingClientRect()).filter(r => r.height);
          return {
            top: heading.getBoundingClientRect().top + window.scrollY,
            bottom: Math.max(...rects.map(r => r.bottom)) + window.scrollY,
            left: Math.min(...rects.map(r => r.left)),
            right: Math.max(...rects.map(r => r.right)),
          };
        }"""
    )
    return {
        "x": b["left"] - PAD,
        # Less padding on top, to leave out the project header border
        "y": b["top"] - 12,
        "width": b["right"] - b["left"] + 2 * PAD,
        "height": b["bottom"] - b["top"] + 12 + PAD,
    }


def element(page, selector, pad=PAD):
    """A single element."""
    b = box(page, selector)
    return {
        "x": b["left"] - pad,
        "y": b["top"] - pad,
        "width": b["right"] - b["left"] + 2 * pad,
        "height": b["bottom"] - b["top"] + 2 * pad,
    }


# --- Community: project settings ------------------------------------------------


@shot("img/screenshot-webhook.png")
def integration_webhook(page):
    busy = SOURCES["busy_project"]
    goto(page, f"{COMMUNITY_URL}/dashboard/{busy}/integrations/{SOURCES['busy_integration']}/")
    page.evaluate(
        """() => {
          document.querySelector('.ui.warning.message')?.remove();
          const times = ['2 minutes ago', '14 minutes ago', '1 hour, 3 minutes ago', '1 hour, 56 minutes ago',
            '3 hours, 12 minutes ago', '5 hours, 40 minutes ago', '1 day, 2 hours ago', '1 day, 4 hours ago',
            '2 days, 1 hour ago', '3 days, 6 hours ago'];
          const header = [...document.querySelectorAll('h3')].find(h => h.textContent.trim() === 'Recent Activity');
          header.nextElementSibling.querySelectorAll('.item').forEach((item, i) => {
            const label = item.querySelector('.ui.label');
            label.className = 'ui green label';
            label.textContent = '200';
            item.querySelector('a').textContent = times[i % times.length];
          });
        }"""
    )
    return above_footer(page)


@shot("img/screenshot_automation_rules_add.png")
def automation_rules(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/rules/create/")
    return main_column(page)


@shot("img/screenshot_environment_variables.png")
def environment_variables(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/environmentvariables/create/")
    return main_column(page)


@shot("img/screenshot_redirects.png")
def redirects(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['busy_project']}/redirects/")
    # Swap external targets (google.com in the dev data) for docs-like paths
    replace_text(
        page,
        [
            ["/en/latest/redirect", "/en/latest/install.html"],
            ["https://google.com", "/en/latest/installation.html"],
            ["/en/full-feature/redirect", "/en/latest/faq.html"],
            ["https://www.google.com", "/en/latest/help/faq.html"],
        ],
    )
    return main_column(page)


@shot("img/screenshot_redirects_preview.png")
def redirects_preview(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/redirects/create/")
    # Use the real form so the preview is generated by the dashboard itself
    page.locator("#id_redirect_type").locator("xpath=..").click()
    page.locator(".menu .item", has_text="Page Redirect").first.click()
    page.locator("#id_from_url").fill("/old.html")
    page.locator("#id_to_url").fill("/new.html")
    page.locator("#id_to_url").blur()
    return main_column(page)


@shot("img/screenshot-howto-build-configuration-file.png")
def build_configuration_file(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/edit/")
    field = "#div_id_readthedocs_yaml_path"
    page.locator("#id_readthedocs_yaml_path").fill("docs/.readthedocs.yaml")
    page.locator(field).evaluate(
        f"el => {{ el.style.outline = '3px solid {HIGHLIGHT}'; el.style.outlineOffset = '8px'; el.style.borderRadius = '2px'; }}"
    )
    b = box(page, field)
    prev = page.locator(field).evaluate(
        "el => el.previousElementSibling.getBoundingClientRect().top + window.scrollY"
    )
    nxt = page.locator(field).evaluate(
        "el => el.nextElementSibling.getBoundingClientRect().bottom + window.scrollY"
    )
    return {
        "x": b["left"] - 2 * PAD,
        "y": prev - PAD,
        "width": b["right"] - b["left"] + 4 * PAD,
        "height": nxt - prev + 2 * PAD,
    }


def fill_queries(page, queries):
    page.evaluate(
        """queries => {
          document.querySelectorAll('table tbody tr').forEach((row, i) => {
            if (i >= queries.length) { row.remove(); return; }
            const [term, results, searches] = queries[i];
            row.querySelector('.header .content').textContent = term;
            const items = row.querySelectorAll('.horizontal.list .item');
            items[0].textContent = `${results} results`;
            items[1].textContent = `${searches} queries`;
          });
        }""",
        queries,
    )


def fill_pages(page, pages):
    page.evaluate(
        """pages => {
          const tbody = document.querySelector('table tbody');
          const template = tbody.querySelector('tr');
          const original = template.querySelector('a').textContent.trim();
          tbody.replaceChildren();
          for (const [path, views] of pages) {
            const row = template.cloneNode(true);
            const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
              const node = walker.currentNode;
              if (node.nodeValue.trim() === original) node.nodeValue = path;
              if (/^\\d[\\d,]* views?$/.test(node.nodeValue.trim())) node.nodeValue = `${views} views`;
            }
            tbody.append(row);
          }
        }""",
        pages,
    )


CHART_SEGMENT = 'canvas >> xpath=ancestor::*[contains(@class,"segment")][1]'


@shot("_static/images/search-analytics-demo.png")
def search_analytics(page):
    chart_data(page, daily_series(48, seed=1))
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['busy_project']}/search-analytics/")
    fill_queries(
        page,
        [
            ["install", 31, 84],
            ["configuration", 16, 77],
            ["theme", 16, 73],
            ["pdf", 12, 56],
            ["redirects", 9, 51],
            ["custom domain", 4, 50],
        ],
    )
    page.wait_for_timeout(1500)
    return content_column(page, 'text="Search Analytics"', CHART_SEGMENT)


@shot("_static/images/addons-analytics.png")
def traffic_analytics(page):
    chart_data(page, daily_series(420, seed=2))
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['busy_project']}/traffic-analytics/")
    fill_pages(
        page,
        [
            ["/index.html", "4,182"],
            ["/installation.html", "2,307"],
            ["/tutorial/index.html", "1,594"],
            ["/configuration.html", "1,120"],
            ["/api/index.html", "863"],
            ["/changelog.html", "412"],
        ],
    )
    page.wait_for_timeout(1500)
    return content_column(page, 'text="Traffic Analytics"', CHART_SEGMENT)


def webhook_page(page):
    project = SOURCES["webhook_project"]
    goto(page, f"{COMMUNITY_URL}/dashboard/{project}/webhooks/{SOURCES['webhook']}/edit/")
    url = page.locator("#id_url").input_value()
    replace_text(page, [[url, "https://example.com/webhooks/readthedocs/"], [project, PROJECT]])
    # Never publish the real secret
    page.locator("#id_secret").evaluate("el => el.value = '7tt135QRvfzCxjRLR8kfE1EXR607TwnO'")


@shot("img/screenshots/community-project-webhook-create.png")
def webhook_create(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/webhooks/create/")
    return main_column(page)


@shot("img/screenshots/community-project-webhook-activity.png")
def webhook_activity(page):
    webhook_page(page)
    # Sample activity, built with the same markup as the template
    page.evaluate(
        """() => {
          const header = [...document.querySelectorAll('h3')].find(h => h.textContent.trim() === 'Recent activity');
          const list = header.nextElementSibling.querySelector('.ui.list');
          const rows = [['200', '2 minutes ago'], ['200', '1 hour, 12 minutes ago'], ['200', '3 hours, 40 minutes ago'],
                        ['404', '1 day, 2 hours ago'], ['200', '2 days, 5 hours ago']];
          list.replaceChildren(...rows.map(([code, when]) => {
            const item = document.createElement('div');
            item.className = 'item';
            item.innerHTML = `<span class="ui ${code === '200' ? 'green' : 'red'} label">${code}</span> <a href="#">${when}</a>`;
            return item;
          }));
        }"""
    )
    return content_column(
        page,
        'text="Recent activity"',
        'xpath=//h3[normalize-space()="Recent activity"]/following-sibling::div[1]',
    )


@shot("img/screenshots/community-project-webhook-secret.png")
def webhook_secret(page):
    webhook_page(page)
    return element(page, "#div_id_secret")


def subproject_page(page):
    parent = SOURCES["subproject_parent"]
    goto(page, f"{COMMUNITY_URL}/dashboard/{parent}/subprojects/")
    replace_text(
        page, [[r"https?://[\w.-]*devthedocs\.(org|com)", "https://docs.example.com"]], regex=True
    )
    replace_text(page, [[parent, PROJECT]])


@shot("img/screenshots/community-project-subproject-create.png")
def subproject_create(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['project']}/subprojects/create/")
    return main_column(page)


@shot("img/screenshots/community-project-subproject-list.png")
def subproject_list(page):
    subproject_page(page)
    return main_column(page)


@shot("img/screenshots/community-edit-button.png", scale=2)
def subproject_edit_button(page):
    subproject_page(page)
    return element(page, "table .ui.icon.buttons > .button >> nth=0", pad=0)


@shot("img/screenshots/community-delete-button.png", scale=2)
def subproject_delete_button(page):
    subproject_page(page)
    return element(page, "table .ui.icon.buttons > .button >> nth=1", pad=0)


# --- Community: account ---------------------------------------------------------


@shot("img/screenshot_connected_services.png")
def connected_services(page):
    goto(page, f"{COMMUNITY_URL}/accounts/social/connections/")
    page.evaluate(
        """([avatar, username]) => {
          const rows = [...document.querySelectorAll('table tbody tr')].filter(r => r.querySelector('.ui.label'));
          const logins = {'GitHub': '2 days ago', 'GitLab': '3 weeks ago', 'Bitbucket': '2 months ago'};
          for (const row of rows) {
            const label = row.querySelector('.ui.label');
            const provider = label.textContent.trim().replace(' OAuth', '');
            label.lastChild.nodeValue = ' ' + provider;
            const content = row.querySelector('.header .content');
            content.firstChild.nodeValue = username;
            content.querySelector('.sub.header').textContent = 'Logged in ' + (logins[provider] || '2 days ago');
            for (const btn of row.querySelectorAll('.button')) {
              if (btn.textContent.trim() === 'Migrate') btn.remove();
            }
            const img = row.querySelector('img');
            if (img) {
              img.src = avatar;
            } else {
              // Rows without an avatar show an icon instead
              const icon = row.querySelector('.header > .icon, .header > i, .header > .image');
              const newImg = Object.assign(document.createElement('img'),
                {className: 'ui rounded image', width: 28, height: 28, src: avatar});
              icon ? icon.replaceWith(newImg) : row.querySelector('.header').prepend(newImg);
            }
          }
          const github = rows.find(r => r.querySelector('.ui.label').textContent.includes('GitHub'));
          if (github) github.parentElement.prepend(github);
        }""",
        [AVATAR, USERNAME],
    )
    page.wait_for_load_state("networkidle")
    return main_column(page)


# --- Business -------------------------------------------------------------------


def business_team_dropdown(page):
    """Open "Add project" (manual) with generic organization names."""
    goto(page, f"{BUSINESS_URL}/dashboard/import/manual/")
    page.evaluate(
        """names => {
          const seen = [];
          for (const item of document.querySelectorAll('#div_id_organization_team-organization_team .menu .item')) {
            const description = item.querySelector('.description');
            const original = description.textContent.trim();
            if (!seen.includes(original)) seen.push(original);
            description.textContent = names[seen.indexOf(original) % names.length];
          }
        }""",
        ORGANIZATIONS,
    )


@shot("img/screenshots/business-project-manual-team-select.png", instance="business")
def business_team_select(page):
    business_team_dropdown(page)
    page.add_style_tag(
        content="footer, .footer { display: none !important; } "
        "#div_id_organization_team-organization_team .menu { max-height: none !important; }"
    )
    page.locator("#div_id_organization_team-organization_team .ui.dropdown").click()
    page.locator(f'.menu .item[data-value="{SOURCES["business_team"]}"]').hover()
    page.wait_for_timeout(500)
    # Semantic UI pre-selects the first item; keep only the hovered one highlighted
    page.evaluate(
        """() => document.querySelectorAll('#div_id_organization_team-organization_team .menu .item.selected')
          .forEach(el => el.classList.remove('selected'))"""
    )
    return content_column(
        page, 'text="Add project"', "#div_id_organization_team-organization_team .menu"
    )


@shot("img/screenshots/business-project-manual-form.png", instance="business")
def business_manual_form(page):
    business_team_dropdown(page)
    page.locator("#div_id_organization_team-organization_team .ui.dropdown").click()
    page.locator(f'.menu .item[data-value="{SOURCES["business_team"]}"]').click()
    # Moving to the next wizard step only stores data in the session
    page.locator('input[type="submit"]').first.click()
    page.wait_for_load_state("networkidle")
    tidy(page)
    page.locator('input[name="basics-name"]').fill(PROJECT)
    page.locator('input[name="basics-repo"]').fill("git@github.com:readthedocs/readthedocs.org.git")
    page.mouse.click(5, 5)
    return content_column(page, 'text="Add project"', 'input[type="submit"] >> nth=-1')


@shot("img/screenshots/business-project-ssh-key.png", instance="business")
def business_ssh_key(page):
    project = SOURCES["business_ssh_project"]
    goto(page, f"{BUSINESS_URL}/dashboard/{project}/keys/{SOURCES['business_ssh_key']}/")
    # Never publish a real key or fingerprint
    replace_text(
        page,
        [
            [r"([0-9a-f]{2}:){15}[0-9a-f]{2}", "01:23:45:67:89:ab:cd:ef:01:23:45:67:89:ab:cd:ef"],
            [r"^ssh-\S+ \S+.*$", "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC" + "0" * 64],
        ],
        regex=True,
    )
    replace_text(page, [[project, PROJECT]])
    return content_column(
        page,
        'xpath=//*[self::h1 or self::h2][contains(normalize-space(), "SSH keys")]',
        'xpath=(//input | //textarea)[last()]/ancestor::div[contains(@class,"field")][1]',
    )


# --- Tutorial (project shown as "tutorial") ------------------------------------


def tutorial_names(page):
    """Rename the sample projects to ``tutorial`` (exact matches only)."""
    page.evaluate(
        """names => {
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const node = walker.currentNode;
            if (names.includes(node.nodeValue.trim())) {
              node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), 'tutorial');
            }
          }
        }""",
        [PROJECT, SOURCES["project"], SOURCES["busy_project"]],
    )


@shot("_static/images/tutorial/rtd-empty-dashboard.png")
def tutorial_empty_dashboard(page):
    goto(page, f"{COMMUNITY_URL}/dashboard/")
    # Same markup as the template's empty state (includes/crud/table_list.html)
    page.evaluate(
        """() => {
          const placeholder = document.createElement('div');
          placeholder.className = 'ui placeholder segment';
          placeholder.innerHTML = `
            <div class="ui icon header"><i class=" icon"></i>You don't have any projects configured yet</div>
            <div class="inline"><a href="#" class="ui primary button">Learn how to get started</a></div>`;
          document.querySelector('table').closest('.segment').replaceWith(placeholder);
          document.querySelector('.ui.pagination.menu')?.remove();
        }"""
    )
    return above_footer(page)


@shot("_static/images/tutorial/rtd-import-projects.png")
def tutorial_import(page):
    fake_api(
        page,
        "**/api/v3/remote/repositories/**",
        {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "pk": 1,
                    "name": TUTORIAL_PROJECT,
                    "full_name": f"{USERNAME}/{TUTORIAL_PROJECT}",
                    "description": "Tutorial project for Read the Docs",
                    "admin": True,
                    "avatar_url": AVATAR,
                    "ssh_url": f"git@github.com:{USERNAME}/{TUTORIAL_PROJECT}.git",
                    "clone_url": f"{TUTORIAL_REPO}.git",
                    "html_url": TUTORIAL_REPO,
                    "vcs": "git",
                    "vcs_provider": "github",
                    "private": False,
                    "default_branch": "main",
                    "projects": [],
                    "remote_organization": None,
                }
            ],
        },
    )
    goto(page, f"{COMMUNITY_URL}/dashboard/import/")
    # Semantic UI search only reacts to key events, not to fill()
    page.locator("xpath=//label[contains(., 'Repository name')]/following::input[1]").click()
    page.keyboard.type(TUTORIAL_PROJECT, delay=80)
    page.locator(".results .result:visible").first.click()
    page.wait_for_timeout(800)
    page.mouse.click(5, 5)
    return above_footer(page)


def tutorial_build_page(page):
    goto(
        page, f"{COMMUNITY_URL}/projects/{SOURCES['busy_project']}/builds/{SOURCES['busy_build']}/"
    )
    tutorial_names(page)
    recent_times(page)
    # Make the build log look like the tutorial template's build
    replace_text(
        page,
        [
            [r"https://github\.com/\S+\.git", f"{TUTORIAL_REPO}.git"],
            [
                r"/home/docs/checkouts/[^/]+/envs/",
                "/home/docs/checkouts/readthedocs.org/user_builds/tutorial/envs/",
            ],
            [r"-r requirements\.txt", "-r docs/requirements.txt"],
            [r"cat docs/conf\.py", "cat docs/source/conf.py"],
            [r" \. \$READTHEDOCS_OUTPUT", " docs/source $READTHEDOCS_OUTPUT"],
        ],
        regex=True,
    )
    set_counters(page, versions=1, builds=1)


@shot("_static/images/tutorial/rtd-first-successful-build.png")
def tutorial_first_build(page):
    tutorial_build_page(page)
    # The first build uses the template's Python version
    replace_text(
        page,
        [[r"asdf global python \S+", f"asdf global python {TUTORIAL_PYTHON_TEMPLATE}"]],
        regex=True,
    )
    return above_footer(page)


@shot("_static/images/tutorial/build-python.png")
def tutorial_build_python(page):
    tutorial_build_page(page)
    page.locator(
        "xpath=//*[starts-with(normalize-space(text()), 'python -mvirtualenv')]"
    ).first.click()
    page.wait_for_timeout(800)
    replace_text(
        page,
        [
            [
                r"/home/docs/checkouts/[^/]+/envs/",
                "/home/docs/checkouts/readthedocs.org/user_builds/tutorial/envs/",
            ]
        ],
        regex=True,
    )
    start = "xpath=//*[starts-with(normalize-space(text()), 'asdf global python')]"
    end = "xpath=//*[starts-with(normalize-space(text()), 'python -m pip install --upgrade --no-cache-dir pip')]"
    top = box(page, start)["top"]
    bottom = box(page, end)["bottom"]
    log = box(page, f"{start}/ancestor::*[contains(@class,'segment')][1]")
    return {
        "x": log["left"],
        "y": top - 6,
        "width": log["right"] - log["left"],
        "height": bottom - top + 12,
    }


def tutorial_versions(page, keep_stable):
    goto(page, f"{COMMUNITY_URL}/projects/{SOURCES['project']}/")
    tutorial_names(page)
    recent_times(page, when="5 minutes ago")
    if keep_stable:
        set_counters(page, versions=2, builds=3)
        return
    page.evaluate(
        """() => {
          for (const row of document.querySelectorAll('table tbody tr')) {
            if (row.querySelector('a')?.textContent.trim() === 'stable') row.remove();
          }
        }"""
    )
    set_counters(page, versions=1, builds=1)
    # Same build number as the first build screenshot
    replace_text(page, [[r"#\d+", f"#{SOURCES['busy_build']}"]], regex=True)


@shot("_static/images/tutorial/rtd-project-home.png")
def tutorial_project_home(page):
    tutorial_versions(page, keep_stable=False)
    return above_footer(page)


@shot("_static/images/tutorial/active-versions.png")
def tutorial_active_versions(page):
    tutorial_versions(page, keep_stable=True)
    return above_footer(page)


@shot("_static/images/tutorial/inactive-versions.png")
def tutorial_inactive_versions(page):
    project = SOURCES["project"]
    version = lambda name, active, identifier: {  # noqa: E731
        "verbose_name": name,
        "slug": name,
        "type": "branch",
        "active": active,
        "identifier": identifier,
        "urls": {"dashboard": {"edit": "#"}},
    }
    fake_api(
        page,
        f"**/api/v3/projects/{project}/versions/**",
        {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                version("1.0.x", False, "1.0.x"),
                version("stable", True, "1.0.x"),
                version("latest", True, "main"),
            ],
        },
    )
    goto(page, f"{COMMUNITY_URL}/dashboard/{project}/version/create/")
    tutorial_names(page)
    set_counters(page, versions=2, builds=3)
    # Results show on focus
    page.locator('input[placeholder="Search versions"]').click()
    page.wait_for_timeout(1500)
    page.locator(".results .result").first.hover()
    return above_footer(page)


@shot("_static/images/tutorial/traffic-analytics-plot.png")
def tutorial_traffic(page):
    chart_data(page, daily_series(35, seed=3))
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['busy_project']}/traffic-analytics/")
    tutorial_names(page)
    fill_pages(
        page,
        [
            ["/index.html", "412"],
            ["/usage.html", "238"],
            ["/api.html", "171"],
            ["/generated/lumache.html", "96"],
        ],
    )
    page.wait_for_timeout(1500)
    return content_column(page, 'text="Traffic Analytics"', CHART_SEGMENT)


@shot("_static/images/tutorial/search-analytics-terms.png")
def tutorial_search(page):
    chart_data(page, daily_series(6, seed=4))
    goto(page, f"{COMMUNITY_URL}/dashboard/{SOURCES['busy_project']}/search-analytics/")
    tutorial_names(page)
    # "ingredients" returns 2 results, as the tutorial says
    fill_queries(
        page,
        [
            ["ingredients", 2, 14],
            ["recipes", 3, 9],
            ["lumache", 4, 7],
            ["installation", 1, 5],
            ["random", 2, 3],
            ["kind", 1, 2],
        ],
    )
    page.wait_for_timeout(1500)
    return content_column(page, 'text="Search Analytics"', CHART_SEGMENT)


# --- External pages (no dev instance needed) -------------------------------------

BROWSER_FRAME = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  body { margin: 0; background: #fff; font-family: system-ui, sans-serif; }
  .window { width: WIDTHpx; border: 1px solid #c8c8c8; border-radius: 8px; overflow: hidden; }
  .bar { display: flex; align-items: center; gap: 10px; height: 40px; padding: 0 12px;
         background: #f0f0f0; border-bottom: 1px solid #d5d5d5; }
  .dots span { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 6px; }
  .url { flex: 1; height: 26px; line-height: 26px; padding: 0 12px; border-radius: 13px;
         background: #fff; color: #333; font-size: 13px; border: 1px solid #ddd; }
  .url .lock { color: #777; margin-right: 6px; }
  img { display: block; }
</style></head><body>
<div class="window">
  <div class="bar">
    <div class="dots"><span style="background:#ff5f57"></span><span style="background:#febc2e"></span><span style="background:#28c840"></span></div>
    <div class="url"><span class="lock">&#128274;</span>URL</div>
  </div>
  <img src="data:image/png;base64,IMAGE">
</div>
</body></html>"""


@shot("_static/images/tutorial/rtd-first-light.png", instance="external")
def tutorial_first_light(page):
    """Live docs built from the tutorial template, framed with a fake address bar."""
    width = 1100
    page.set_viewport_size({"width": width, "height": 860})
    page.goto(SOURCES["tutorial_live_docs"], wait_until="networkidle")
    page.wait_for_timeout(3000)
    # That copy has extra pages that aren't part of the tutorial template
    page.evaluate(
        """() => document.querySelectorAll('a').forEach(a => {
          if (a.textContent.trim() === 'Using Chinese') a.closest('li').remove();
        })"""
    )
    image = base64.b64encode(page.screenshot()).decode()
    html = (
        BROWSER_FRAME.replace("WIDTH", str(width))
        .replace("URL", TUTORIAL_URL)
        .replace("IMAGE", image)
    )
    page.set_viewport_size({"width": width + 40, "height": 1000})
    page.set_content(html)
    return element(page, ".window", pad=0)


# --- Runner ------------------------------------------------------------------------


def instance_is_up(context, instance):
    """Check the instance answers with this session, and is the expected product."""
    if instance == "external":
        return True
    if not SESSIONS[instance]:
        print(f"skipping {instance}: set RTD_{instance.upper()}_SESSIONID", file=sys.stderr)
        return False
    try:
        response = context.request.get(
            f"{base(instance)}/dashboard/", max_redirects=0, fail_on_status_code=False
        )
        page = response.text().replace(" ", "").replace("\n", "")
    except Error:
        response, page = None, ""
    badge = "Community" if instance == "community" else "Business"
    if not response or response.status != 200 or f">{badge}<" not in page:
        print(
            f"skipping {instance}: {base(instance)} isn't running or isn't logged in",
            file=sys.stderr,
        )
        return False
    return True


def launch(playwright):
    channel = os.environ.get("PLAYWRIGHT_CHANNEL", "chrome")
    try:
        return playwright.chromium.launch(channel=channel)
    except Exception:
        # Fall back to Playwright's bundled Chromium (``uv run playwright install chromium``)
        return playwright.chromium.launch()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "filters", nargs="*", help="only screenshots whose path contains any of these"
    )
    parser.add_argument("--list", action="store_true", help="list screenshots and exit")
    parser.add_argument(
        "--out", type=Path, default=DOCS_USER, help="output directory (default: docs/user)"
    )
    args = parser.parse_args()

    selected = [s for s in SHOTS if not args.filters or any(f in s["path"] for f in args.filters)]
    if args.list:
        for s in selected:
            print(f"{s['instance']:10} {s['path']}  ({s['func'].__name__})")
        return

    with sync_playwright() as playwright:
        browser = launch(playwright)
        available = {}
        for s in selected:
            context = browser.new_context(
                viewport={"width": WIDTH, "height": 900},
                device_scale_factor=s["scale"],
                color_scheme="light",
            )
            context.add_cookies(
                [
                    {"name": "sessionid", "value": value, "url": base(instance)}
                    for instance, value in SESSIONS.items()
                    if value
                ]
            )
            if s["instance"] not in available:
                available[s["instance"]] = instance_is_up(context, s["instance"])
            if not available[s["instance"]]:
                context.close()
                continue

            page = context.new_page()
            clip = s["func"](page)
            page.wait_for_timeout(800)
            out = (args.out / s["path"]).resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=out, full_page=True, clip=clip)
            print("wrote", out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out)
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
