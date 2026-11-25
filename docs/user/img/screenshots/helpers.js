// Shared by all screenshots: the Makefile injects this file into each entry's
// javascript (the HELPERS placeholder). It tidies the page and defines helpers.
document.documentElement.dataset.theme = "light";
for (const img of document.querySelectorAll('img[src*="gravatar.com"]')) {
  img.src = "https://assets.readthedocs.org/static/images/silhouette.png";
}
const _style = document.createElement("style");
_style.textContent = "readthedocs-notification, #djDebug { display: none !important; }";
document.head.append(_style);
// Organization and "Unofficial" badges in the project header, staff-only Debug tab
for (const el of document.querySelectorAll('a.ui.label[href*="/organizations/"]')) el.remove();
for (const el of document.querySelectorAll(".ui.label, a.item")) {
  if (["Unofficial", "Debug"].includes(el.textContent.trim())) el.remove();
}
[...document.querySelectorAll("h2")]
  .find((h) => h.textContent.trim() === "Help topics")
  ?.closest(".segment")
  ?.remove();
for (const el of document.querySelectorAll("input")) {
  el.value = el.value.replace(/https?:\/\/devthedocs\.(org|com)/g, "https://app.readthedocs.org");
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function until(check, timeout = 10000) {
  for (let waited = 0; waited < timeout; waited += 100) {
    const value = check();
    if (value) return value;
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${check}`);
}

function replaceText(pairs, regex = false) {
  const swap = (s) =>
    pairs.reduce((acc, [a, b]) => (regex ? acc.replace(new RegExp(a, "gm"), b) : acc.replaceAll(a, b)), s);
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) walker.currentNode.nodeValue = swap(walker.currentNode.nodeValue);
  for (const el of document.querySelectorAll("input, textarea")) el.value = swap(el.value);
}

// Show the projects borrowed from the database as "docs"
for (const slug of new Set(["${PROJECT}", "${BUSY_PROJECT}"])) {
  if (slug !== "docs") replaceText([[slug, "docs"]]);
}

function recentTimes(when = "2 minutes ago") {
  replaceText([[String.raw`\b(a|an|\d+)\s+(year|month|week|day|hour)s?(,\s*\d+\s+\w+)?\s+ago\b`, when]], true);
}

function setCounters(versions, builds) {
  for (const item of document.querySelectorAll("a.item")) {
    const label = item.querySelector(".label");
    if (!label) continue;
    if (item.textContent.trim().startsWith("Versions")) label.textContent = versions;
    if (item.textContent.trim().startsWith("Builds")) label.textContent = builds;
  }
}

// Exact rename only, so "docs" inside other words is kept
function renameExact(names, to) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (names.includes(node.nodeValue.trim())) node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), to);
  }
}

// Set a form field the way typing would, so Knockout sees it
function setValue(selector, value) {
  const el = document.querySelector(selector);
  el.value = value;
  for (const type of ["input", "change", "blur"]) el.dispatchEvent(new Event(type, { bubbles: true }));
}

// The element with a text node of exactly this text, like Playwright's text="..."
function byText(text, root = document.body) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    if (walker.currentNode.nodeValue.trim() === text) return walker.currentNode.parentElement;
  }
}

// The input of a field shown with a header, like "Webhook URL"
function fieldInput(header) {
  return byText(header)?.closest(".content")?.querySelector("input");
}

// Business pages shown as Community: product badge and Business-only links
function asCommunity() {
  // Same as the template, includes/utils/site_label.html
  for (const label of document.querySelectorAll(".ui.violet.label")) {
    if (label.textContent.trim() !== "Business") continue;
    label.textContent = "Community";
    label.classList.replace("violet", "teal");
  }
  for (const el of document.querySelectorAll("a.item")) {
    if (["Organizations", "Sharing", "SSH keys"].includes(el.textContent.trim())) el.remove();
  }
}

function removePagination() {
  document.querySelectorAll(".ui.pagination.menu").forEach((el) => el.remove());
}

function xpath(expression) {
  return document.evaluate(expression, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
}

// 31 days of plausible numbers: weekday highs, weekend dips, some noise
function dailySeries(average, seed) {
  let state = seed;
  const random = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  return Array.from({ length: 31 }, (_, day) => {
    const weekend = [5, 6].includes(day % 7);
    const trend = 1 + 0.15 * Math.sin((day / 31) * Math.PI);
    return Math.round(average * trend * (0.85 + 0.3 * random()) * (weekend ? 0.45 : 1));
  });
}

async function chartData(values) {
  const chart = await until(() => window.Chart && Object.values(Chart.instances)[0]);
  chart.data.datasets[0].data = values;
  chart.update(0);
}

function fillQueries(queries) {
  removePagination();
  document.querySelectorAll("table tbody tr").forEach((row, i) => {
    if (i >= queries.length) return row.remove();
    const [term, results, searches] = queries[i];
    row.querySelector(".header .content").textContent = term;
    const items = row.querySelectorAll(".horizontal.list .item");
    items[0].textContent = `${results} results`;
    items[1].textContent = `${searches} queries`;
  });
}

function fillPages(pages) {
  removePagination();
  const tbody = document.querySelector("table tbody");
  const template = tbody.querySelector("tr");
  const original = template.querySelector("a").textContent.trim();
  tbody.replaceChildren();
  for (const [path, views] of pages) {
    const row = template.cloneNode(true);
    const walker = document.createTreeWalker(row, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.nodeValue.trim() === original) node.nodeValue = path;
      if (/^\d[\d,]* views?$/.test(node.nodeValue.trim())) node.nodeValue = `${views} views`;
    }
    tbody.append(row);
  }
}

// Search fields get sample results instead of calling the API
function fakeSearch(search, results) {
  jQuery(search).search("setting", "apiSettings", {
    mockResponse: { count: results.length, next: null, previous: null, results },
  });
}

// --- Crop: entries use `selector: "#shot"`, an invisible box over the area ---

const PAD = 16;

function box(el) {
  const r = el.getBoundingClientRect();
  return { top: r.top + scrollY, bottom: r.bottom + scrollY, left: r.left, right: r.right };
}

function clip(rect) {
  // Whole pixels, so the box isn't snapped one pixel larger
  const [x, y, width, height] = [rect.x, rect.y, rect.width, rect.height].map(Math.round);
  const div = document.createElement("div");
  div.id = "shot";
  Object.assign(div.style, {
    position: "absolute",
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`,
    pointerEvents: "none",
  });
  document.body.append(div);
}

// The whole page, without the footer
function aboveFooter() {
  clip({ x: 0, y: 0, width: innerWidth, height: box(document.querySelector("footer, .footer")).top });
}

// The main content column: from its heading to the end of its content
function mainColumn() {
  const heading = [...document.querySelectorAll("h2")].find((h) => {
    const column = h.closest(".column");
    return column && !column.querySelector(".ui.vertical.menu") && h.offsetHeight;
  });
  const rects = [...heading.closest(".column").children].map(box).filter((r) => r.bottom > r.top);
  const top = box(heading).top;
  const bottom = Math.max(...rects.map((r) => r.bottom));
  const left = Math.min(...rects.map((r) => r.left));
  const right = Math.max(...rects.map((r) => r.right));
  // Less padding on top, to leave out the project header border
  clip({ x: left - PAD, y: top - 12, width: right - left + 2 * PAD, height: bottom - top + 12 + PAD });
}

// The right-hand content column, between two elements
function contentColumn(topEl, bottomEl) {
  const top = box(topEl);
  const bottom = box(bottomEl);
  // 1200: right edge of the dashboard container at 1280 pixels
  clip({
    x: top.left - PAD,
    y: top.top - PAD,
    width: 1200 - top.left + 2 * PAD,
    height: bottom.bottom - top.top + 2 * PAD,
  });
}

function element(el, pad = PAD) {
  const b = box(el);
  clip({ x: b.left - pad, y: b.top - pad, width: b.right - b.left + 2 * pad, height: b.bottom - b.top + 2 * pad });
}
