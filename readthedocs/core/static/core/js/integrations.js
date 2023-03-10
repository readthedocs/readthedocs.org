// Unique entry point that our servers will inject

// Load Read the Docs data first
// This data is generated at build time by the doctool
fetch("/en/manual-integration-docsify/readthedocs-data.html", {method: 'GET'})
    .then(response => {
        return response.text();
    })
    .then(text => {
        document.head.insertAdjacentHTML("beforeend", text);
    });

// TODO: use `READTHEDOCS_DATA.features.hosting.version` to decide
// what version of these Javascript libraries we need to inject here.
// See https://github.com/readthedocs/readthedocs.org/issues/9063#issuecomment-1325483505
let link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", "/_/static/css/readthedocs-doc-embed.css");
document.head.appendChild(link);

let embed = document.createElement("script");
embed.setAttribute("async", "async");
embed.setAttribute("src", "/_/static/javascript/readthedocs-doc-embed.js");
document.head.appendChild(embed);

let analytics = document.createElement("script");
analytics.setAttribute("async", "async");
analytics.setAttribute("src", "/_/static/javascript/readthedocs-analytics.js");
document.head.appendChild(analytics);

let hosting = document.createElement("script");
hosting.setAttribute("async", "async");
hosting.setAttribute("src", "/_/static/core/js/readthedocs-hosting.js");
document.head.appendChild(hosting);

// TODO: insert search-as-you-type once it becomes a JS library
// decoupled from Sphinx.
// See https://github.com/readthedocs/readthedocs-sphinx-search/issues/67

// TODO: find a way to remove the Sphinx default search, since it duplicates the results sometimes.
// This removal is currently happening at our Sphinx extension:
// https://github.com/readthedocs/readthedocs-sphinx-ext/blob/7cc1e60f7dcdeb7af35e3479509a621d5bac0976/readthedocs_ext/readthedocs.py#L239
