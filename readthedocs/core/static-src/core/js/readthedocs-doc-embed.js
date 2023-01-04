const sponsorship = require('./doc-embed/sponsorship');
const footer = require('./doc-embed/footer.js');
// grokthedocs = require('./doc-embed/grokthedocs-client'),
// mkdocs = require('./doc-embed/mkdocs'),
const sphinx = require('./doc-embed/sphinx');
const search = require('./doc-embed/search');
const { domReady } = require('./doc-embed/utils');

/*
 * Inject JQuery if isn't present already.
 *
 * Parts of this script rely on JQuery (mainly the flyout menu injection),
 * since Sphinx no longer includes it, and other tools may not include it,
 * we must inject it if isn't found before executing our script.
*/
function injectJQuery(init) {
    if (window.jQuery) {
        init()
        return
    }
    console.debug("JQuery not found. Injecting.");
    var script = document.createElement("script");
    script.type = "text/javascript";
    script.src = "https://code.jquery.com/jquery-3.6.3.min.js";
    script.integrity = "sha512-STof4xm1wgkfm7heWqFJVn58Hm3EtS31XFaagaa8VMReCXAkQnJZ+jEy8PCC/iT18dFy95WcExNHFTqLyp72eQ==";
    script.crossOrigin = "anonymous";
    script.onload = init;
    document.head.appendChild(script);
}


(function () {
    domReady(function () {
        // Block on jQuery loading before we run any of our code.
        injectJQuery(function() {
            footer.init();
            sphinx.init();
            search.init();
            sponsorship.init();
        })
    });
}());
