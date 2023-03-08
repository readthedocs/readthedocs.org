// Unique entry point that our servers will inject

let link = document.createElement("link");
link.setAttribute("rel", "stylesheet");
link.setAttribute("type", "text/css");
link.setAttribute("href", "/_/static/css/readthedocs-doc-embed.css");
document.head.appendChild(link);

let script = document.createElement("script");
script.setAttribute("async", "async");
script.setAttribute("src", "/_/static/javascript/readthedocs-doc-embed.js");
document.head.appendChild(script);
