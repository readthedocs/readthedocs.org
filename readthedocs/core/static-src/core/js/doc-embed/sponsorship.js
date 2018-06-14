/* Read the Docs - Documentation promotions */

var constants = require('./constants');
var rtddata = require('./rtd-data');

var bowser = require('bowser');

var rtd;

/*
 *  Creates a sidebar div where an ad could go
 */
function create_sidebar_placement() {
    var element_id = 'rtd-' + (Math.random() + 1).toString(36).substring(4);
    var display_type = constants.PROMO_TYPES.LEFTNAV;
    var priority = constants.DEFAULT_PROMO_PRIORITY;
    var selector = null;
    var class_name;         // Used for theme specific CSS customizations
    var offset;

    if (rtd.is_mkdocs_builder() && rtd.is_rtd_theme()) {
        selector = 'nav.wy-nav-side';
        class_name = 'ethical-rtd';
    } else if (rtd.is_rtd_theme()) {
        selector = 'nav.wy-nav-side > div.wy-side-scroll';
        class_name = 'ethical-rtd';
    } else if (rtd.get_theme_name() === constants.THEME_ALABASTER ||
               rtd.get_theme_name() === constants.THEME_CELERY) {
        selector = 'div.sphinxsidebar > div.sphinxsidebarwrapper';
        class_name = 'ethical-alabaster';
    }

    if (selector) {
        $('<div />').attr('id', element_id)
            .addClass(class_name).appendTo(selector);

        // Determine if this element is above the fold
        offset = $('#' + element_id).offset();
        if (!offset || offset.top > $(window).height()) {
            // If this is off screen, lower the priority
            priority = constants.LOW_PROMO_PRIORITY;
        }

        return {
            'div_id': element_id,
            'display_type': display_type,
            'priority': priority,
        };
    }

    return null;
}

/*
 *  Creates a sidebar div where an ad could go
 *  Returns the ID of the div or none if no footer ad is possible
 */
function create_footer_placement() {
    var element_id = 'rtd-' + (Math.random() + 1).toString(36).substring(4);
    var display_type = constants.PROMO_TYPES.FOOTER;
    var priority = constants.DEFAULT_PROMO_PRIORITY;
    var selector = null;
    var class_name;
    var offset;

    if (rtd.is_rtd_theme()) {
        selector = $('<div />').insertAfter('footer hr');
        class_name = 'ethical-rtd';
    } else if (rtd.get_theme_name() === constants.THEME_ALABASTER ||
               rtd.get_theme_name() === constants.THEME_CELERY) {
        selector = 'div.bodywrapper .body';
        class_name = 'ethical-alabaster';
    }

    if (selector) {
        $('<div />').attr('id', element_id)
            .addClass(class_name).appendTo(selector);

        // Determine if this element is above the fold
        offset = $('#' + element_id).offset();
        if (!offset || offset.top < $(window).height()) {
            // If the screen is short, lower the priority
            // We don't want the ad to take up too much of the screen
            priority = constants.LOW_PROMO_PRIORITY;
        }

        return {
            'div_id': element_id,
            'display_type': display_type,
            'priority': priority,
        };
    }

    return null;
}

/*
 *  Creates a fixed footer placmenet
 *  Returns the ID of the div or none if a fixed footer ad shouldn't be used
 */
function create_fixed_footer_placement() {
    var element_id = 'rtd-' + (Math.random() + 1).toString(36).substring(4);
    var display_type = constants.PROMO_TYPES.FIXED_FOOTER;

    // Only propose the fixed footer ad for mobile
    if (bowser && bowser.mobile) {
        $('<div />').attr('id', element_id).appendTo('body');
        return {
            'div_id': element_id,
            'display_type': display_type,

            // Prioritize mobile ads when on mobile
            'priority': constants.MAXIMUM_PROMO_PRIORITY,
        };
    }

    return null;
}

function Promo(data) {
    this.id = data.id;                              // analytics id
    this.div_id = data.div_id || '';
    this.html = data.html || '';
    this.display_type = data.display_type || '';

    // Handler when a promo receives a click
    this.click_handler = function () {
        // This needs to handle both old style legacy analytics for previously built docs
        // as well as the newer universal analytics
        if (typeof ga !== 'undefined') {
            ga('rtfd.send', 'event', 'Promo', 'Click', data.id);
        } else if (typeof _gaq !== 'undefined') {
            _gaq.push(
                ['rtfd._setAccount', 'UA-17997319-1'],
                ['rtfd._trackEvent', 'Promo', 'Click', data.id]
            );
        }
    };
}

/*
 *  Position and inject the promo
 */
Promo.prototype.display = function () {
    $('#' + this.div_id).html(this.html);
    $('#' + this.div_id).find('a[href*="/sustainability/click/"]')
        .on('click', this.click_handler);

    this.post_promo_display();
};

Promo.prototype.disable = function () {
    $('#' + this.div_id).hide();
};

/*
 * Perform any additional tweaks after the ad is successfully injected
 */
Promo.prototype.post_promo_display = function () {
    if (this.display_type === constants.PROMO_TYPES.FOOTER) {
        $('<hr />').insertAfter('#' + this.div_id);

        // Alabaster only
        $('<hr />').insertBefore('#' + this.div_id + '.ethical-alabaster .ethical-footer');
    }
};

function adblock_admonition() {
    console.log('---------------------------------------------------------------------------------------');
    console.log('Read the Docs hosts documentation for tens of thousands of open source projects.');
    console.log('We fund our development (we are open source) and operations through advertising.');

    console.log('We promise to:');
    console.log(' - never let advertisers run 3rd party JavaScript');
    console.log(' - never sell user data to advertisers or other 3rd parties');
    console.log(' - only show advertisements of interest to developers');
    console.log('Read more about our approach to advertising here: https://docs.readthedocs.io/en/latest/ethical-advertising.html');
    console.log('Read more about Ads for Open Source: https://ads-for-open-source.readthedocs.io');
    console.log('Or go ad-free: https://readthedocs.org/sustainability/');
    console.log('%cPlease whitelist Read the Docs on your adblocker using the following filter:', 'font-size: 2em');
    console.log('https://ads-for-open-source.readthedocs.io/en/latest/_static/lists/readthedocs-ads.txt');
    console.log('--------------------------------------------------------------------------------------');
}

function adblock_nag() {
    // Place an ad block nag into the sidebar
    var placement = create_sidebar_placement();
    var unblock_url = 'https://ads-for-open-source.readthedocs.io/';
    var ad_free_url = 'https://readthedocs.org/sustainability/';
    var container = null;

    if (placement && placement.div_id) {
        container = $('#' + placement.div_id).attr('class', 'keep-us-sustainable');

        $('<p />').text('Support Read the Docs!').appendTo(container);
        $('<p />').html('Please help keep us sustainable by <a href="' + unblock_url + '">allowing our Ethical Ads in your ad blocker</a> or <a href="' + ad_free_url + '">go ad-free</a> by subscribing.').appendTo(container);
        $('<p />').text('Thank you! \u2764\ufe0f').appendTo(container);
    }
}

function init() {
    var request_data = {format: "jsonp"};
    var div_ids = [];
    var display_types = [];
    var priorities = [];
    var placement_funcs = [
        create_footer_placement,
        create_sidebar_placement,
        create_fixed_footer_placement,
    ];
    var params;
    var placement;

    rtd = rtddata.get();

    if (!rtd.show_promo()) {
        return;
    }

    for (var i = 0; i < placement_funcs.length; i += 1) {
        placement = placement_funcs[i]();
        if (placement) {
            div_ids.push(placement.div_id);
            display_types.push(placement.display_type);
            priorities.push(placement.priority || constants.DEFAULT_PROMO_PRIORITY);
        }
    }

    request_data.div_ids = div_ids.join('|');
    request_data.display_types = display_types.join('|');
    request_data.priorities = priorities.join('|');
    request_data.project = rtd.project;

    if (typeof URL !== 'undefined' && typeof URLSearchParams !== 'undefined') {
        // Force a specific promo to be displayed
        params = new URL(window.location).searchParams;
        if (params.get('force_promo')) {
            request_data.force_promo = params.get('force_promo');
        }

        // Force a promo from a specific campaign
        if (params.get('force_campaign')) {
            request_data.force_campaign = params.get('force_campaign');
        }
    }

    // Request a promo to inject onto the page
    $.ajax({
        url: rtd.api_host + "/api/v2/sustainability/",
        crossDomain: true,
        xhrFields: {
            withCredentials: true,
        },
        dataType: "jsonp",
        data: request_data,
        success: function (data) {
            var promo;
            if (data && data.div_id && data.html) {
                promo = new Promo(data);
                promo.display();
            }
        },
        error: function (xhr, textStatus, errorThrown) {
            console.error('Error loading Read the Docs promo');

            if (xhr && xhr.status === 404 && rtd.api_host === 'https://readthedocs.org') {
                adblock_admonition();
                adblock_nag();
            }
        },
    });
}

module.exports = {
    Promo: Promo,
    init: init,
};
