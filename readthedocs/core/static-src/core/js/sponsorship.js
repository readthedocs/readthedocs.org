/* Read the Docs - Documentation promotions */

var $ = window.$,
    waypoint = require('waypoints'),
    Waypoint = window.Waypoint;

module.exports = {
    Promo: Promo
};

function Promo (text, link) {
    this.text = text;
    this.link = link;
    this.promo = null;
    this.waypoint = null;
}

Promo.prototype.create = function () {
    var nav_side = $('nav.wy-nav-side');

    if (nav_side.length) {
        // Add elements
        promo = $('<div />')
            .attr('class', 'wy-menu rst-pro');

        // Create link with callback
        var promo_link = $('<a />')
            .attr('class', 'rst-pro-link')
            .attr('href', this.link)
            .html(this.text)
            .appendTo(promo);

        // Promo info
        var promo_about = $('<div />')
            .attr('class', 'rst-pro-about');
        var promo_about_link = $('<a />')
            .attr('href', 'http://docs.readthedocs.org/')
            .appendTo(promo_about);
        var promo_about_icon = $('<i />')
            .attr('class', 'fa fa-info-circle')
            .appendTo(promo_about_link);
        promo_about.appendTo(promo);

        promo.appendTo(nav_side);

        return promo;
    }
}

// Position class management
Promo.prototype.display_fixed = function () {
    this.promo
        .removeClass('rst-pro-static')
        .addClass('rst-pro-fixed');
}

Promo.prototype.display_static = function () {
    this.promo
        .removeClass('rst-pro-fixed')
        .addClass('rst-pro-static');
}

// Position promo
Promo.prototype.display = function (sliding) {
    var promo = this.promo,
        self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }

    if (sliding) {
        Waypoint.destroyAll();
        this.waypoint = new Waypoint({
            element: promo.get(0),
            offset: function () {
                return $(window).height() - promo.height() - 80;
            },
            handler: function (direction) {
                if (direction == 'down') {
                    self.display_fixed();
                }
                else if (direction == 'up') {
                    self.display_static();
                }
            }
        });
    }
    else {
        if (this.waypoint) {
            this.waypoint.remove();
            this.waypoint = null;
        }
        this.display_fixed();
    }
}
