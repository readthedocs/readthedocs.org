/* Read the Docs - Documentation promotions */

var constants = require('./constants');
var rtddata = require('./rtd-data');
const { createDomNode } = require('./utils');

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
    var class_name = "";  // Used for theme specific CSS customizations
    var style_name = "";
    var ad_type = "readthedocs-sidebar";

    let placement = document.querySelector(EXPLICIT_PLACEMENT_SELECTOR);
    if (placement) {
        placement.setAttribute("data-ea-publisher", "readthedocs")
        placement.setAttribute("data-ea-manual", "true");
        let ea_type = placement.getAttribute("data-ea-type");
        if (ea_type !== "image" && ea_type !== "text") {
            placement.setAttribute("data-ea-type", "readthedocs-sidebar");
        }
        return placement;
    }

    placement = document.querySelector(OLD_EXPLICIT_PLACEMENT_SELECTOR);
    if (placement) {
        if (rtd.is_rtd_like_theme()) {
            class_name = 'ethical-rtd ethical-dark-theme';
        } else {
            class_name = 'ethical-alabaster';
        }
    } else if (rtd.is_mkdocs_builder() && rtd.is_rtd_like_theme()) {
        placement = document.querySelector('nav.wy-nav-side');
        class_name = 'ethical-rtd ethical-dark-theme';
    } else if (rtd.is_rtd_like_theme()) {
        placement = document.querySelector('nav.wy-nav-side > div.wy-side-scroll');
        class_name = 'ethical-rtd ethical-dark-theme';
    } else if (rtd.is_alabaster_like_theme()) {
        placement = document.querySelector('div.sphinxsidebar > div.sphinxsidebarwrapper');
        class_name = 'ethical-alabaster';
    }

    if (placement) {
        // Determine if this element would be above the fold
        // If this is off screen, instead create an ad in the footer
        // Assumes the ad would be ~200px high
        let aux_element = createDomNode("div");
        placement.appendChild(aux_element);
        let position = aux_element.getBoundingClientRect()
        if ((position.top + 200) > window.innerHeight) {
            if (rtd.is_rtd_like_theme()) {
                placement = createDomNode("div");
                let rtd_footer = document.querySelector('footer hr');
                rtd_footer.insertAfter(placement)
                class_name = 'ethical-rtd';

                // Use the stickybox placement 25% of the time during rollout
                // But only when the ad would be in the footer
                if (Math.random() <= 0.25) {
                    style_name = 'stickybox';
                    ad_type = 'image';
                }
            } else if (rtd.is_alabaster_like_theme()) {
                placement = document.querySelector('div.bodywrapper .body');
                class_name = 'ethical-alabaster';
            }
        }
        aux_element.remove();

        // Add the element where the ad will go
        let ad_div = createDomNode("div", {
          "id": 'rtd-sidebar',
          "data-ea-publisher": "readthedocs",
          "data-ea-type": ad_type,
          "data-ea-manual": "true",
          "data-ea-style": style_name,
          "class": class_name,
        });
        placement.appendChild(ad_div)
        return ad_div;
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

    if (placement) {
        let container = placement.setAttribute('class', 'keep-us-sustainable');
        let paragraph = createDomNode("p");
        paragraph.innerText = 'Support Read the Docs!';
        container.appendChild(paragraph);
        
        paragraph = createDomNode("p");
        paragraph.innerHTML = 'Please help keep us sustainable by <a href="' + unblock_url + '">allowing our Ethical Ads in your ad blocker</a> or <a href="' + ad_free_url + '">go ad-free</a> by subscribing.';
        container.appendChild(paragraph);

        paragraph = createDomNode("p");
        paragraph.innerText = 'Thank you! \u2764\ufe0f';
        container.appendChild(paragraph);
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
                placement.setAttribute("data-ea-keywords", data.keywords.join("|"));
            }
            if (data.campaign_types) {
                placement.setAttribute("data-ea-campaign-types", data.campaign_types.join("|"));
            }
            if (data.publisher) {
                placement.setAttribute("data-ea-publisher", data.publisher);
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
                document.getElementById("ethicaladsjs").addEventListener("load", function () {
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
