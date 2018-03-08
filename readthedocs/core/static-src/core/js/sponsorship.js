/* Read the Docs - Documentation promotions */

var constants = require('./doc-embed/constants');


function Promo (id, text, link, image, theme, display_type, pixel) {
    this.id = id;       // analytics id
    this.text = text;
    this.link = link;
    this.image = image;
    this.theme = theme || constants.THEME_RTD;
    this.display_type = display_type || constants.PROMO_TYPES.LEFTNAV;
    this.pixel = pixel;
    this.promo = null;

    // Handler when a promo receives a click
    this.click_handler = function () {
        // This needs to handle both old style legacy analytics for previously built docs
        // as well as the newer universal analytics
        if (typeof ga !== 'undefined') {
            ga('rtfd.send', 'event', 'Promo', 'Click', id);
        } else if (typeof _gaq !== 'undefined') {
            _gaq.push(
                ['rtfd._setAccount', 'UA-17997319-1'],
                ['rtfd._trackEvent', 'Promo', 'Click', id]
            );
        }
    };
}

Promo.prototype.create = function () {
    var self = this;
    var menu;
    var promo_class;
    if (this.theme === constants.THEME_RTD) {
        menu = this.get_sphinx_rtd_theme_promo_selector();
        promo_class = this.display_type === constants.PROMO_TYPES.FOOTER ? 'rtd-pro-footer' : 'wy-menu';
    }
    else if (this.theme === constants.THEME_ALABASTER || this.theme === constants.THEME_CELERY) {
        menu = this.get_alabaster_promo_selector();
        promo_class = this.display_type === constants.PROMO_TYPES.FOOTER ? 'rtd-pro-footer' : 'alabaster';
    }

    if (typeof(menu) !== 'undefined') {
        this.place_promo(menu, promo_class);
    }
}

Promo.prototype.place_promo = function (selector, promo_class) {
    var self = this;

    // Add elements
    var promo = $('<div />')
        .attr('class', 'rtd-pro ' + promo_class);

    // Promo info
    var promo_about = $('<div />')
        .attr('class', 'rtd-pro-about');
    var promo_about_link = $('<a />')
        .attr('href', 'https://readthedocs.org/sustainability/advertising/')
        .appendTo(promo_about);
    $('<span />').text('Sponsored ').appendTo(promo_about_link);
    var promo_about_icon = $('<i />')
        .attr('class', 'fa fa-info-circle')
        .appendTo(promo_about_link);
    promo_about.appendTo(promo);

    // Promo image
    if (self.pixel) {
        // Use a first-party tracking pixel for text ads,
        // so we can still count the number of times they are displayed
        var pixel = $('<img />')
            .attr('style', 'display: none;')
            .attr('src', self.image)
            .appendTo(promo);
    } else {
        var promo_image_link = $('<a />')
            .attr('class', 'rtd-pro-image-wrapper')
            .attr('href', self.link)
            .attr('target', '_blank')
            .attr('rel', 'nofollow')
            .on('click', self.click_handler);
        var promo_image = $('<img />')
            .attr('class', 'rtd-pro-image')
            .attr('src', self.image)
            .appendTo(promo_image_link);
        promo.append(promo_image_link);
    }

    // Create link with callback
    var promo_text = $('<span />')
        .html(self.text);
    $(promo_text).find('a').each(function () {
        $(this)
            .attr('class', 'rtd-pro-link')
            .attr('href', self.link)
            .attr('target', '_blank')
            .attr('rel', 'nofollow')
            .on('click', self.click_handler);
    });
    promo.append(promo_text);

    var copy_text = $(
    '<p class="ethical-callout"><small><em><a href="https://docs.readthedocs.io/en/latest/ethical-advertising.html">' +
    'Ads served ethically' +
    '</a></em></small></p>'
    )
    promo.append(copy_text);


    promo.appendTo(selector);

    promo.wrapper = $('<div />')
        .attr('class', 'rtd-pro-wrapper')
        .appendTo(selector);

    return promo;
};

Promo.prototype.get_alabaster_promo_selector = function () {
    // Return a jQuery selector where the promo goes on the Alabaster theme
    var self = this;
    var selector;
    var wrapper;

    if (self.display_type === constants.PROMO_TYPES.FOOTER) {
        wrapper = $('<div />')
            .attr('class', 'rtd-pro-footer-wrapper body')
            .appendTo('div.bodywrapper');
        $('<hr />').appendTo(wrapper);
        selector = $('<div />').appendTo(wrapper);
        $('<hr />').appendTo(wrapper);
    } else {
        selector = $('div.sphinxsidebar > div.sphinxsidebarwrapper');
    }

    if (selector.length) {
        return selector;
    }
};


Promo.prototype.get_sphinx_rtd_theme_promo_selector = function () {
    // Return a jQuery selector where the promo goes on the RTD theme
    var self = this;
    var selector;

    if (self.display_type === constants.PROMO_TYPES.FOOTER) {
        selector = $('<div />')
            .attr('class', 'rtd-pro-footer-wrapper')
            .insertBefore('footer hr');
        $('<hr />').insertBefore(selector);
    } else {
        selector = $('nav.wy-nav-side > div.wy-side-scroll');
    }

    if (selector.length) {
        return selector;
    }
};

// Position promo
Promo.prototype.display = function () {
    var promo = this.promo;
    var self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }

    // Promo still might not exist yet
    if (promo) {
        promo.show();
    }
};

Promo.prototype.disable = function () {
};

// Variant factory method
Promo.from_variants = function (variants) {
    if (variants.length === 0) {
        return null;
    }
    var chosen = Math.floor(Math.random() * variants.length);
    var variant = variants[chosen];
    var text = variant.text;
    var link = variant.link;
    var image = variant.image;
    var id = variant.id;
    return new Promo(id, text, link, image);
};

module.exports = {
    Promo: Promo
};
