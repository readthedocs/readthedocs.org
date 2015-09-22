/*
 * Sphinx builder specific JS code.
 */


var rtddata = require('./rtd-data'),
    sphinx_theme = require('sphinx-rtd-theme');


function init() {
    var rtd = rtddata.get();

    /// Click tracking on flyout
    $(document).on('click', "[data-toggle='rst-current-version']", function() {
      var flyout_state = $("[data-toggle='rst-versions']").hasClass('shift-up') ? 'was_open' : 'was_closed'
      if (_gaq) {
        _gaq.push(
            ['rtfd._setAccount', 'UA-17997319-1'],
            ['rtfd._trackEvent', 'Flyout', 'Click', flyout_state]
        );
      }
    });

    /// Read the Docs Sphinx theme code
    if (!("builder" in rtd) || "builder" in rtd && rtd["builder"] != "mkdocs") {
        var theme = sphinx_theme.ThemeNav;

        // Because generated HTML will not immediately have the new scroll
        // element, gracefully handle failover by adding it dynamically.
        var navBar = jquery('div.wy-side-scroll:first');
        if (! navBar.length) {
            var navInner = jquery('nav.wy-nav-side:first'),
                navScroll = $('<div />')
                    .addClass('wy-side-scroll');

            navInner
                .children()
                .detach()
                .appendTo(navScroll);
            navScroll.prependTo(navInner);

            theme.navBar = navScroll;
        }
    }

}


module.exports = {
    init: init
};
