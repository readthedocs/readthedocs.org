/* Read the Docs - Documentation house ads */

// Jquery hack for now
var $ = window.$,
    waypoint = require('waypoints'),
    Waypoint = window.Waypoint;

module.exports = {
    Ad: Ad
};

function Ad (text, link, callback) {
    this.ad_text = text;
    this.ad_link = link;
    this.ad_callback = callback;
}

Ad.prototype.display_ad = function () {
    var nav_side = $('nav.wy-nav-side');

    if (nav_side.length) {
        // Add elements
        var nav_ad = $('<div />')
            .css({
                padding: '.5em',
                margin: '1em 0em',
                background: 'rgba(0, 0, 0, .06)'
            })
            .attr('class', 'wy-menu rst-adv');

        // Create link with callback
        var ad_link = $('<a />')
            .css({
                display: 'block',
                'font-size': '90%'
            })
            .attr('href', this.ad_link)
            .html(this.ad_text);
        if (typeof this.ad_callback !== 'undefined') {
            ad_link.on('click', this.ad_callback);
        }
        ad_link.appendTo(nav_ad);

        // Ad callout
        var ad_about = $('<p />')
            .css({
                'display': 'block',
                'text-align': 'right',
                'font-size': '80%',
                'color': '#000'
            })
            .html('Ad by Write the Docs')
            .appendTo(nav_ad);

        nav_ad.appendTo(nav_side);

        // Positioning
        var waypoint = new Waypoint({
            element: $('.rst-adv')[0],
            handler: function (direction) {
                if (direction == 'down') {
                    nav_ad.css({
                        position: 'fixed',
                        top: '0px',
                        width: '300px'
                    })
                }
                else if (direction == 'up') {
                    nav_ad.css({
                        position: 'static'
                    })
                }
            }
        });
    }
}
