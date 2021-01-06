/* Read the Docs - Documentation promotions */

var constants = require('./constants');
var rtddata = require('./rtd-data');

var rtd;

var EXPLICIT_PLACEMENT_SELECTOR = "[data-ea-publisher]";

// Old way to control the exact placement of an ad
var OLD_EXPLICIT_PLACEMENT_SELECTOR = '#ethical-ad-placement';


/*
 * Inject the EthicalAds ad client
 */
function inject_ads_client() {
    var script = document.createElement("script");
    script.src = "https://media.ethicalads.io/media/client/beta/ethicalads.min.js";
    script.type = "text/javascript";
    script.async = true;
    script.id = "ethicaladsjs";
    document.getElementsByTagName("head")[0].appendChild(script);
}

/*
 *  Creates a div where the ad could go
 */
function create_ad_placement() {
    var selector = null;
    var class_name;         // Used for theme specific CSS customizations
    var element;
    var offset;

    if ($(EXPLICIT_PLACEMENT_SELECTOR).length > 0) {
        $(EXPLICIT_PLACEMENT_SELECTOR).attr("data-ea-publisher", "readthedocs");
        $(EXPLICIT_PLACEMENT_SELECTOR).attr("data-ea-manual", "true");
        if ($(EXPLICIT_PLACEMENT_SELECTOR).attr("data-ea-type") !== "image" && $(EXPLICIT_PLACEMENT_SELECTOR).attr("data-ea-type") !== "text") {
            $(EXPLICIT_PLACEMENT_SELECTOR).attr("data-ea-type", "readthedocs-sidebar");
        }
        return $(EXPLICIT_PLACEMENT_SELECTOR);
    } else if ($(OLD_EXPLICIT_PLACEMENT_SELECTOR).length > 0) {
        selector = OLD_EXPLICIT_PLACEMENT_SELECTOR;
        if (rtd.is_rtd_like_theme()) {
            class_name = 'ethical-rtd ethical-dark-theme';
        } else {
            class_name = 'ethical-alabaster';
        }
    } else if (rtd.is_mkdocs_builder() && rtd.is_rtd_like_theme()) {
        selector = 'nav.wy-nav-side';
        class_name = 'ethical-rtd ethical-dark-theme';
    } else if (rtd.is_rtd_like_theme()) {
        selector = 'nav.wy-nav-side > div.wy-side-scroll';
        class_name = 'ethical-rtd ethical-dark-theme';
    } else if (rtd.is_alabaster_like_theme()) {
        selector = 'div.sphinxsidebar > div.sphinxsidebarwrapper';
        class_name = 'ethical-alabaster';
    }

    if (selector) {
        // Determine if this element would be above the fold
        // If this is off screen, instead create an ad in the footer
        // Assumes the ad would be ~200px high
        element = $("<div />").appendTo(selector);
        offset = element.offset();
        if (!offset || (offset.top - $(window).scrollTop() + 200) > $(window).height()) {
            if (rtd.is_rtd_like_theme()) {
                selector = $('<div />').insertAfter('footer hr');
                class_name = 'ethical-rtd';
            } else if (rtd.is_alabaster_like_theme()) {
                selector = 'div.bodywrapper .body';
                class_name = 'ethical-alabaster';
            }
        }
        element.remove();

        // Add the element where the ad will go
        return $('<div />')
            .attr("id", "rtd-sidebar")
            .attr("data-ea-publisher", "readthedocs")
            .attr("data-ea-type", "readthedocs-sidebar")
            .attr("data-ea-manual", "true")
            .addClass(class_name)
            .appendTo(selector);
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

function adblock_nag(placement) {
    // Place an ad block nag into the sidebar
    var unblock_url = 'https://docs.readthedocs.io/en/latest/advertising/ad-blocking.html#allowing-ethical-ads';
    var ad_free_url = 'https://readthedocs.org/sustainability/';
    var container = null;

    if (placement) {
        container = placement.attr('class', 'keep-us-sustainable');

        $('<p />').text('Support Read the Docs!').appendTo(container);
        $('<p />').html('Please help keep us sustainable by <a href="' + unblock_url + '">allowing our Ethical Ads in your ad blocker</a> or <a href="' + ad_free_url + '">go ad-free</a> by subscribing.').appendTo(container);
        $('<p />').text('Thank you! \u2764\ufe0f').appendTo(container);
    }
}

function init() {
    var placement;

    rtd = rtddata.get();

    if (!rtd.show_promo()) {
        return;
    }

    placement = create_ad_placement();

    // Inject ads
    inject_ads_client();

    $.ajax({
        url: rtd.api_host + "/api/v2/sustainability/data/",
        crossDomain: true,
        xhrFields: {
            withCredentials: true,
        },
        dataType: "jsonp",
        data: {
            format: "jsonp",
            project: rtd.project,
        },
        success: function (data) {
            if (!placement || data.ad_free) {
                // No valid placement or project/user is ad free
                return;
            }

            // Set the keyword, campaign data, and publisher
            if (data.keywords) {
                placement.attr("data-ea-keywords", data.keywords.join("|"));
            }
            if (data.campaign_types) {
                placement.attr("data-ea-campaign-types", data.campaign_types.join("|"));
            }
            if (data.publisher) {
                placement.attr("data-ea-publisher", data.publisher);
            }

            if (typeof ethicalads !== "undefined") {
                // Trigger ad request
                ethicalads.load();
            } else if (!rtd.ad_free && detect_adblock()) {
                // Ad client prevented from loading - check ad blockers
                adblock_admonition();
                adblock_nag(placement);
            } else {
                // The ad client hasn't loaded yet which could happen due to a variety of issues
                // Add an event listener for it to load
                $("#ethicaladsjs").on("load", function () {
                    if (typeof ethicalads !== "undefined") {
                        ethicalads.load();
                    }
                });
            }
        },
        error: function () {
            console.error('Error loading Read the Docs user and project information');

            if (!rtd.ad_free && detect_adblock()) {
                adblock_admonition();
                adblock_nag(placement);
            }
        },
    });
}

module.exports = {
    init: init,
};
