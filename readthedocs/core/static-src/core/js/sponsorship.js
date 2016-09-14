/* Read the Docs - Documentation promotions */

module.exports = {
    Promo: Promo
};

function Promo (id, text, link, image) {
    this.id = id;
    this.text = text;
    this.link = link;
    this.image = image;
    this.promo = null;
}

Promo.prototype.create = function () {
    var self = this,
        nav_side = $('nav.wy-nav-side > div.wy-side-scroll');

    if (nav_side.length) {
        // Add elements
        promo = $('<div />')
            .attr('class', 'wy-menu rst-pro');

        // Promo info
        var promo_about = $('<div />')
            .attr('class', 'rst-pro-about');
        var promo_about_link = $('<a />')
            .attr('href', 'http://docs.readthedocs.io/en/latest/ethical-advertising.html')
            .appendTo(promo_about);
        var promo_about_icon = $('<i />')
            .attr('class', 'fa fa-info-circle')
            .appendTo(promo_about_link);
        promo_about.appendTo(promo);

        // On Click handler
        function promo_click() {
            if (_gaq) {
                _gaq.push(
                    ['rtfd._setAccount', 'UA-17997319-1'],
                    ['rtfd._trackEvent', 'Promo', 'Click', self.id]
                );
            }
        }

        // Promo image
        if (self.image) {
            var promo_image_link = $('<a />')
                .attr('class', 'rst-pro-image-wrapper')
                .attr('href', self.link)
                .attr('target', '_blank')
                .on('click', promo_click);
            var promo_image = $('<img />')
                .attr('class', 'rst-pro-image')
                .attr('src', self.image)
                .appendTo(promo_image_link);
            promo.append(promo_image_link);
        }

        // Create link with callback
        var promo_text = $('<span />')
            .html(self.text);
        $(promo_text).find('a').each(function () {
            $(this)
                .attr('class', 'rst-pro-link')
                .attr('href', self.link)
                .attr('target', '_blank')
                .on('click', promo_click);
        });
        promo.append(promo_text);

        promo.appendTo(nav_side);

        promo.wrapper = $('<div />')
            .attr('class', 'rst-pro-wrapper')
            .appendTo(nav_side);

        return promo;
    }
}

// Position promo
Promo.prototype.display = function () {
    var promo = this.promo,
        self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }

    // Promo still might not exist yet
    if (promo) {
        promo.show();
    }
}

Promo.prototype.disable = function () {
}

// Variant factory method
Promo.from_variants = function (variants) {
    if (variants.length == 0) {
        return null;
    }
    var chosen = Math.floor(Math.random() * variants.length),
        variant = variants[chosen],
        text = variant.text,
        link = variant.link,
        image = variant.image,
        id = variant.id;
    return new Promo(id, text, link, image);
};
