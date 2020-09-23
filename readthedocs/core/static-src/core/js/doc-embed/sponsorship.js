/* Read the Docs - Documentation promotions */

var constants = require('./constants');
var rtddata = require('./rtd-data');

var rtd;

// Old
var EXPLICIT_PLACEMENT_SELECTOR = '#ethical-ad-placement';


/*
 * Inject the EthicalAds ad client
 */
function inject_ads_client() {
    var script = document.createElement("script");
    script.src = "https://media.ethicalads.io/media/client/beta/ethicalads.min.js";
    script.type = "text/javascript";
    script.async = true;
    document.getElementsByTagName("head")[0].appendChild(script);
}

/*
 *  Creates a sidebar div where an ad could go
 */
function create_ad_placement() {
    var selector = null;
    var class_name;         // Used for theme specific CSS customizations
    var container;

    if (rtd.is_mkdocs_builder() && rtd.is_rtd_like_theme()) {
        selector = 'nav.wy-nav-side';
        class_name = 'dark raised';
    } else if (rtd.is_rtd_like_theme()) {
        selector = 'nav.wy-nav-side > div.wy-side-scroll';
        class_name = 'dark raised';
    } else if (rtd.is_alabaster_like_theme()) {
        selector = 'div.sphinxsidebar > div.sphinxsidebarwrapper';
        class_name = 'raised';
    }

    if (selector) {
        container = $('<div />').attr('style', 'text-align:center').appendTo(selector);
        $('<div />')
            .attr('data-ea-publisher', "readthedocs")
            .attr('data-ea-type', "image")
            .addClass(class_name).appendTo(container);
    }

    return null;
}

function detect_adblock() {
    // Status codes are not correctly reported on JSONP requests
    // So we resort to different ways to detect adblockers
    var detected = false;

    // Check if our ad element is blocked
    $('<div />')
        .attr('id', 'rtd-detection')
        .attr('class', 'ethical-rtd')
        .html('&nbsp;')
        .appendTo('body');
    if ($('#rtd-detection').height() === 0) {
        detected = true;
    }

    // Remove the test element regardless
    $('#rtd-detection').remove();

    return detected;
}

function adblock_admonition() {
    console.log('---------------------------------------------------------------------------------------');
    console.log('Read the Docs hosts documentation for tens of thousands of open source projects.');
    console.log('We fund our development (we are open source) and operations through advertising.');

    console.log('We promise to:');
    console.log(' - never let advertisers run 3rd party JavaScript');
    console.log(' - never sell user data to advertisers or other 3rd parties');
    console.log(' - only show advertisements of interest to developers');
    console.log('Read more about our approach to advertising here: https://docs.readthedocs.io/en/latest/advertising/ethical-advertising.html');
    console.log('%cPlease allow our Ethical Ads or go ad-free:', 'font-size: 2em');
    console.log('https://docs.readthedocs.io/en/latest/advertising/ad-blocking.html');
    console.log('--------------------------------------------------------------------------------------');
}

function init() {
    rtd = rtddata.get();

    // Inject ads
    create_ad_placement();
    inject_ads_client();

    if (detect_adblock()) {
        adblock_admonition();
    }
}

module.exports = {
    init: init,
};
