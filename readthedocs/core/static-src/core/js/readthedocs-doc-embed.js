var sponsorship = require('./doc-embed/sponsorship');
var footer = require('./doc-embed/footer.js');
// grokthedocs = require('./doc-embed/grokthedocs-client'),
// mkdocs = require('./doc-embed/mkdocs'),
var rtddata = require('./doc-embed/rtd-data');
var sphinx = require('./doc-embed/sphinx');
var search = require('./doc-embed/search');

// Adds the $.inViewport function
$.extend(require('verge'));


$(document).ready(function () {
    footer.init();
    sphinx.init();
    // grokthedocs.init();
    // mkdocs.init();
    search.init();
    sponsorship.init();
});
