var rtddata = require('./rtd-data');


function init(data) {
    var rtd = rtddata.get();

    /// Out of date message

    if (data.is_stable) {
        return;
    }

    var message = 'You are not using the most up to date version of the library.';
    if (data.is_highest) {
      message = 'You are not using the stable version of the library.';
    }

    var currentURL = window.location.pathname.replace(rtd['version'], data.slug);
    var warning = $(
        '<div class="admonition warning"> ' +
        '<p class="first admonition-title">Note</p> ' +
        '<p class="last"> ' +
         message + ' ' +
        '<a href="#"></a> is the stable version.' +
        '</p>' +
        '</div>');

    warning
      .find('a')
      .attr('href', currentURL)
      .text(data.version);

    var body = $("div.body");
    if (!body.length) {
        body = $("div.document");
    }
    body.prepend(warning);
}


module.exports = {
    init: init
};
