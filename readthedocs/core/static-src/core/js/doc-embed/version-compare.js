var rtddata = require('./rtd-data');


function init(data) {
    var rtd = rtddata.get();

    /// Out of date message

    if (data.is_highest) {
        return;
    }

    var currentURL = window.location.pathname.replace(rtd['version'], data.slug);
    var warning = $(
        '<div class="admonition warning"> ' +
        '<p class="first admonition-title">Note</p> ' +
        '<p class="last"> ' +
        'You are not reading the most recent version of this documentation. ' +
        '<a href="#"></a> is the latest version available.' +
        '</p>' +
        '</div>');

    warning
      .find('a')
      .attr('href', currentURL)
      .text(data.slug);

    var body = $("div.body");
    if (!body.length) {
        body = $("div.document");
    }
    body.prepend(warning);
}


module.exports = {
    init: init
};
