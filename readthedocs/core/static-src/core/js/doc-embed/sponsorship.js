/* Read the Docs - Documentation promotions */

var constants = require('./constants'),
    rtddata = require('./rtd-data');

var rtd;

function init() {
    var post_data = {},
        force,
        params;

    rtd = rtddata.get();

    if (!rtd.show_promo()) {
        return;
    }

    post_data.placements = get_placements(rtd);
    post_data.project = rtd.project;

    if (typeof URL !== 'undefined' && typeof URLSearchParams !== 'undefined') {
        // Force a specific promo to be displayed
        params = new URL(window.location).searchParams;
        force = params.get('promo');
        if (force) {
            post_data.promo = force;
        }

        // Force a promo from a specific campaign
        force = params.get('campaign');
        if (force) {
            post_data.campaign = force;
        }
    }

    // Request a promo to inject onto the page
    $.ajax({
        url: rtd.api_host + "/api/v2/sustainability/",
        type: 'post',
        xhrFields: {
            withCredentials: true,
        },
        dataType: "json",
        data: JSON.stringify(post_data),
        contentType: "application/json",
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

/*
 *  Returns an array of possible places where a promo could go
 */
function get_placements () {
    var placements = [],
        placement_funcs = [create_footer_placement, create_sidebar_placement],
        placement;

    for (var i = 0; i < placement_funcs.length; i += 1) {
        placement = placement_funcs[i]();
        if (placement) {
            placements.push(placement);
        }
    }

    return placements;
}

/*
 *  Creates a sidebar div where an ad could go
 */
function create_sidebar_placement () {
    var element_id = 'rtd-ethical-sidebar',
        display_type = constants.PROMO_TYPES.LEFTNAV,
        selector = null;

    if (rtd.is_rtd_theme()) {
        selector = 'nav.wy-nav-side > div.wy-side-scroll';
    } else if (rtd.get_theme_name() == constants.THEME_ALABASTER ||
               rtd.get_theme_name() == constants.THEME_CELERY) {
        selector = 'div.sphinxsidebar > div.sphinxsidebarwrapper';
    }

    if (selector) {
        $('<div />').attr('id', element_id).appendTo(selector);
        return {'div_id': element_id, 'display_type': display_type};
    }

    return null;
}

/*
 *  Creates a sidebar div where an ad could go
 *  Returns the ID of the div or none if no footer ad is possible
 */
function create_footer_placement () {
    var element_id = 'rtd-ethical-footer',
        display_type = constants.PROMO_TYPES.FOOTER,
        selector = null;

    if (rtd.is_rtd_theme()) {
        selector = $('<div />').insertAfter('footer hr');
    } else if (rtd.get_theme_name() == constants.THEME_ALABASTER ||
               rtd.get_theme_name() == constants.THEME_CELERY) {
        selector = 'div.bodywrapper';
    }

    if (selector) {
        $('<div />').attr('id', element_id).appendTo(selector);
        return {'div_id': element_id, 'display_type': display_type};
    }

    return null;
}

function Promo (data) {
    this.id = data.id;                              // analytics id
    this.div_id = data.div_id || '';
    this.html = data.html || '';
    this.pixel = data.pixel || '';
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
};

Promo.prototype.disable = function () {
    $('#' + this.div_id).hide();
};

module.exports = {
    Promo: Promo,
    init: init,
};
