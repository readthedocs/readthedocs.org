const sponsorship = require('./doc-embed/sponsorship');
const footer = require('./doc-embed/footer.js');
// grokthedocs = require('./doc-embed/grokthedocs-client'),
// mkdocs = require('./doc-embed/mkdocs'),
const sphinx = require('./doc-embed/sphinx');
const search = require('./doc-embed/search');
const { domReady } = require('./doc-embed/utils');

(function () {
    domReady(function () {
        footer.init();
        sphinx.init();
        search.init();
        sponsorship.init();
    });
}());
