/*

  Script to inject the new Addons implementation on pages served by El Proxito.

  This script is ran on a Cloudflare Worker and modifies the HTML with two different purposes:

      1. remove the old implementation of our flyout (``readthedocs-doc-embed.js`` and others)
      2. inject the new addons implementation (``readthedocs-addons.js``) script

  Currently, we are doing 1) only when users opt-in into the new beta addons.
  In the future, when our addons become stable, we will always remove the old implementation,
  making all the projects to use the addons by default.

*/

// add "readthedocs-addons.js" inside the "<head>"
const addonsJs =
  '<script async type="text/javascript" src="/_/static/javascript/readthedocs-addons.js"></script>';

// selectors we want to remove
// https://developers.cloudflare.com/workers/runtime-apis/html-rewriter/#selectors
const analyticsJs =
  'script[src="/_/static/javascript/readthedocs-analytics.js"]';
const docEmbedCss = 'link[href="/_/static/css/readthedocs-doc-embed.css"]';
const docEmbedJs =
  'script[src="/_/static/javascript/readthedocs-doc-embed.js"]';
const analyticsJsAssets =
  'script[src="https://assets.readthedocs.org/static/javascript/readthedocs-analytics.js"]';
const docEmbedCssAssets =
  'link[href="https://assets.readthedocs.org/static/css/readthedocs-doc-embed.css"]';
const docEmbedJsAssets =
  'script[src="https://assets.readthedocs.org/static/javascript/readthedocs-doc-embed.js"]';
const docEmbedJsAssetsCore =
  'script[src="https://assets.readthedocs.org/static/core/js/readthedocs-doc-embed.js"]';
const badgeOnlyCssAssets =
  'link[href="https://assets.readthedocs.org/static/css/badge_only.css"]';
const badgeOnlyCssAssetsProxied = 'link[href="/_/static/css/badge_only.css"]';
const readthedocsExternalVersionWarning = "[role=main] > div:first-child > div:first-child.admonition.warning";
const readthedocsFlyout = "div.rst-versions";

// "readthedocsDataParse" is the "<script>" that calls:
//
//   READTHEDOCS_DATA = JSON.parse(document.getElementById('READTHEDOCS_DATA').innerHTML);
//
const readthedocsDataParse = "script[id=READTHEDOCS_DATA]:first-of-type";
const readthedocsData = "script[id=READTHEDOCS_DATA]";

// do this on a fetch
addEventListener("fetch", (event) => {
  const request = event.request;
  event.respondWith(handleRequest(request));
});

async function handleRequest(request) {
  // perform the original request
  let originalResponse = await fetch(request);

  // get the content type of the response to manipulate the content only if it's HTML
  const contentType = originalResponse.headers.get("content-type") || "";
  const injectHostingIntegrations =
    originalResponse.headers.get("x-rtd-hosting-integrations") || "false";
  const forceAddons =
    originalResponse.headers.get("x-rtd-force-addons") || "false";

  // Log some debugging data
  console.log(`ContentType: ${contentType}`);
  console.log(`X-RTD-Force-Addons: ${forceAddons}`);
  console.log(`X-RTD-Hosting-Integrations: ${injectHostingIntegrations}`);

  // get project/version slug from headers inject by El Proxito
  const projectSlug = originalResponse.headers.get("x-rtd-project") || "";
  const versionSlug = originalResponse.headers.get("x-rtd-version") || "";

  // check to decide whether or not inject the new beta addons:
  //
  // - content type has to be "text/html"
  // when all these conditions are met, we remove all the old JS/CSS files and inject the new beta flyout JS

  // check if the Content-Type is HTML, otherwise do nothing
  if (contentType.includes("text/html")) {
    // Remove old implementation of our flyout and inject the new addons if the following conditions are met:
    //
    // - header `X-RTD-Force-Addons` is present (user opted-in into new beta addons)
    // - header `X-RTD-Hosting-Integrations` is not present (added automatically when using `build.commands`)
    //
    if (forceAddons === "true" && injectHostingIntegrations === "false") {
      return (
        new HTMLRewriter()
          .on(analyticsJs, new removeElement())
          .on(docEmbedCss, new removeElement())
          .on(docEmbedJs, new removeElement())
          .on(analyticsJsAssets, new removeElement())
          .on(docEmbedCssAssets, new removeElement())
          .on(docEmbedJsAssets, new removeElement())
          .on(docEmbedJsAssetsCore, new removeElement())
          .on(badgeOnlyCssAssets, new removeElement())
          .on(badgeOnlyCssAssetsProxied, new removeElement())
          .on(readthedocsExternalVersionWarning, new removeElement())
          .on(readthedocsFlyout, new removeElement())
          // NOTE: I wasn't able to reliably remove the "<script>" that parses
          // the "READTHEDOCS_DATA" defined previously, so we are keeping it for now.
          //
          // .on(readthedocsDataParse, new removeElement())
          // .on(readthedocsData, new removeElement())
          .on("head", new addPreloads())
          .on("head", new addProjectVersionSlug(projectSlug, versionSlug))
          .transform(originalResponse)
      );
    }

    // Inject the new addons if the following conditions are met:
    //
    // - header `X-RTD-Hosting-Integrations` is present (added automatically when using `build.commands`)
    // - header `X-RTD-Force-Addons` is not present (user opted-in into new beta addons)
    //
    if (forceAddons === "false" && injectHostingIntegrations === "true") {
      return new HTMLRewriter()
        .on("head", new addPreloads())
        .on("head", new addProjectVersionSlug(projectSlug, versionSlug))
        .transform(originalResponse);
    }
  }

  // Modify `_static/searchtools.js` to re-enable Sphinx's default search
  if (
    (contentType.includes("text/javascript") ||
      contentType.includes("application/javascript")) &&
    (injectHostingIntegrations === "true" || forceAddons === "true") &&
    originalResponse.url.endsWith("_static/searchtools.js")
  ) {
    console.log("Modifying _static/searchtools.js");
    return handleSearchToolsJSRequest(originalResponse);
  }

  // if none of the previous conditions are met,
  // we return the response without modifying it
  return originalResponse;
}

class removeElement {
  element(element) {
    console.log("Removing: " + element.tagName);
    console.log("Attribute href: " + element.getAttribute("href"));
    console.log("Attribute src: " + element.getAttribute("src"));
    console.log("Attribute id: " + element.getAttribute("id"));
    console.log("Attribute class: " + element.getAttribute("class"));
    element.remove();
  }
}

class addPreloads {
  element(element) {
    console.log("addPreloads");
    element.append(addonsJs, { html: true });
  }
}

class addProjectVersionSlug {
  constructor(projectSlug, versionSlug) {
    this.projectSlug = projectSlug;
    this.versionSlug = versionSlug;
  }

  element(element) {
    console.log(
      `addProjectVersionSlug. projectSlug=${this.projectSlug} versionSlug=${this.versionSlug}`,
    );
    if (this.projectSlug && this.versionSlug) {
      const metaProject = `<meta name="readthedocs-project-slug" content="${this.projectSlug}" />`;
      const metaVersion = `<meta name="readthedocs-version-slug" content="${this.versionSlug}" />`;

      element.append(metaProject, { html: true });
      element.append(metaVersion, { html: true });
    }
  }
}

/*

  Script to fix the old removal of the Sphinx search init.

  Enabling addons breaks the default Sphinx search in old versions that are not possible to rebuilt.
  This is because we solved the problem in the `readthedocs-sphinx-ext` extension,
  but since those versions can't be rebuilt, the fix does not apply there.

  To solve the problem in these old versions, we are using a CF worker to apply that fix on-the-fly
  at serving time on those old versions.

  The fix basically replaces a Read the Docs comment in file `_static/searchtools.js`,
  introduced by `readthedocs-sphinx-ext` to _disable the initialization of Sphinx search_,
  with the real JavaScript to initialize the search, as Sphinx does by default.
  (in other words, it _reverts_ the manipulation done by `readthedocs-sphinx-ext`)

*/

const textToReplace = `/* Search initialization removed for Read the Docs */`;
const textReplacement = `
/* Search initialization manipulated by Read the Docs using Cloudflare Workers */
/* See https://github.com/readthedocs/addons/issues/219 for more information */

function initializeSearch() {
  Search.init();
}

if (document.readyState !== "loading") {
  initializeSearch();
}
else {
  document.addEventListener("DOMContentLoaded", initializeSearch);
}
`;

async function handleSearchToolsJSRequest(originalResponse) {
  const content = await originalResponse.text();
  const modifiedResponse = new Response(
    content.replace(textToReplace, textReplacement),
  );
  return modifiedResponse;
}
