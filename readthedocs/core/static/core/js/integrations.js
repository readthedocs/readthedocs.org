// Unique entry point that our servers will inject

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
