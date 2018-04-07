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
    var selector = null;
    var class_name;         // Used for theme specific CSS customizations

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
        return {'div_id': element_id, 'display_type': display_type};
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
    var selector = null;
    var class_name;

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
        return {'div_id': element_id, 'display_type': display_type};
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
        return {'div_id': element_id, 'display_type': display_type};
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

function init() {
    var request_data = {format: "jsonp"};
    var div_ids = [];
    var display_types = [];
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
        }
    }

    request_data.div_ids = div_ids.join('|');
    request_data.display_types = display_types.join('|');
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
        error: function () {
            console.error('Error loading Read the Docs promo');
        },
    });
}

module.exports = {
    Promo: Promo,
    init: init,
};
