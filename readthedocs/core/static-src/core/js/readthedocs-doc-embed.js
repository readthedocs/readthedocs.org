const sponsorship = require('./doc-embed/sponsorship');
// grokthedocs = require('./doc-embed/grokthedocs-client'),
// mkdocs = require('./doc-embed/mkdocs'),
const sphinx = require('./doc-embed/sphinx');
const search = require('./doc-embed/search');
const { domReady } = require('./doc-embed/utils');
const rtddata = require('./doc-embed/rtd-data');

/*
 * Inject JQuery if isn't present already.
 *
 * Parts of this script rely on JQuery (mainly the flyout menu injection),
 * since Sphinx no longer includes it, and other tools may not include it,
 * we must inject it if isn't found before executing our script.
*/
function injectJQuery(init) {
    if (window.jQuery) {
        init();
        return;
    }
    console.debug("JQuery not found. Injecting.");
    let rtd = rtddata.get();
    let script = document.createElement("script");
    script.type = "text/javascript";
    script.src = rtd.proxied_static_path + "vendor/jquery.js";
    script.onload = function () {
        // Set jQuery to its expected globals.
        /* eslint-disable global-require */
        window.$ = require("jquery");
        window.jQuery = window.$;
        init();
    };
    document.head.appendChild(script);
}


(function () {
    domReady(function () {
        // Block on jQuery loading before we run any of our code.
        injectJQuery(function () {
            sphinx.init();
            search.init();
            sponsorship.init();
        });
    });
}());
