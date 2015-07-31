var sponsorship = require('./sponsorship'),
    doc = require('./doc'),
    footer = require('./doc-embed/footer.js'),
    grokthedocs = require('./doc-embed/grokthedocs-client'),
    mkdocs = require('./doc-embed/mkdocs'),
    rtddata = require('./doc-embed/rtd-data'),
    sphinx = require('./doc-embed/sphinx');

$(document).ready(function () {
    var build = new doc.Build(rtddata.get());

    footer.init(build);
    sphinx.init();
    grokthedocs.init();
    mkdocs.init();
});
