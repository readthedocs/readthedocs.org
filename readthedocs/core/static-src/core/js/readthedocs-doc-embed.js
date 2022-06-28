var sponsorship = require('./doc-embed/sponsorship');
var footer = require('./doc-embed/footer.js');
// grokthedocs = require('./doc-embed/grokthedocs-client'),
// mkdocs = require('./doc-embed/mkdocs'),
var rtddata = require('./doc-embed/rtd-data');
var sphinx = require('./doc-embed/sphinx');
var search = require('./doc-embed/search');


// Parts of this script rely on jQuery,
// since Sphinx no longer includes it,
// we must inject it if isn't found before executing our script.
(function () {
    function domReady(fn) {
        // If the DOM is already done parsing
        if (document.readyState === "complete" || document.readyState === "interactive") {
            setTimeout(fn, 1);
        } else {
            document.addEventListener("DOMContentLoaded", fn);
        }
    }

    function init() {
        footer.init();
        sphinx.init();
        search.init();
        sponsorship.init();
    }

    domReady(function () {
      // Inject JQuery if isn't present already.
      if (!window.jQuery) {
          console.log("JQuery not found. Injecting.");
          var script = document.createElement("script");
          script.type = "text/javascript";
          script.src = "https://code.jquery.com/jquery-3.6.0.min.js";
          script.integrity = "sha512-894YE6QWD5I59HgZOGReFYm4dnWc1Qt5NtvYSaNcOP+u1T9qYdvdihz0PPSiiqn/+/3e7Jo4EaG7TubfWGUrMQ==";
          script.crossOrigin = "anonymous";
          script.onload = init;
          document.head.appendChild(script);
      } else {
          init();
      }
    });
}());
