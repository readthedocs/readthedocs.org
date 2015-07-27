var sponsorship = require('./sponsorship'),
    doc = require('./doc'),
    footer = require('./doc-embed/footer.js'),
    grokthedocs = require('./doc-embed/grokthedocs-client'),
    mkdocs = require('./doc-embed/mkdocs'),
    rtd = require('./doc-embed/rtd-data'),
    sphinx = require('./doc-embed/sphinx'),
    versionCompare = require('./doc-embed/version-compare');

$(document).ready(function () {
    var build = new doc.Build(rtd);

    footer.init(build);
    sphinx.init();
    grokthedocs.init();
    versionCompare.init();
    mkdocs.init();
});
