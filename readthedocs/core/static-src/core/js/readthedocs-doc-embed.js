var sponsorship = require('./sponsorship'),
    footer = require('./doc-embed/footer.js'),
    // grokthedocs = require('./doc-embed/grokthedocs-client'),
    mkdocs = require('./doc-embed/mkdocs'),
    rtddata = require('./doc-embed/rtd-data'),
    sphinx = require('./doc-embed/sphinx'),
    search = require('./doc-embed/search');

$(document).ready(function () {
    footer.init();
    sphinx.init();
    // grokthedocs.init();
    mkdocs.init();
    search.init();
});
