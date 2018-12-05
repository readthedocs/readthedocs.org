/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */

var constants = require('./constants');

var configMethods = {
    is_rtd_like_theme: function () {
        // Returns true for the Read the Docs theme on both sphinx and mkdocs
        if ($('div.rst-other-versions').length === 1) {
            // Crappy heuristic, but people change the theme name
            // So we have to do some duck typing.
            return true;
        }
        return this.theme === constants.THEME_RTD || this.theme === constants.THEME_MKDOCS_RTD;
    },

    is_alabaster_like_theme: function () {
        // Returns true for Alabaster-like themes (eg. flask, celery)
        return constants.ALABASTER_LIKE_THEMES.indexOf(this.get_theme_name()) > -1;
    },

    theme_supports_promo: function () {
        return this.is_rtd_like_theme() || this.is_alabaster_like_theme();
    },

    is_sphinx_builder: function () {
        return (!('builder' in this) || this.builder !== 'mkdocs');
    },

    is_mkdocs_builder: function () {
        return ('builder' in this && this.builder === 'mkdocs');
    },

    get_theme_name: function () {
        return this.theme;
    },

    show_promo: function () {
        return (
            this.api_host !== 'https://readthedocs.com' &&
            this.theme_supports_promo());
    }
};


/*
 * Access READTHEDOCS_DATA on call, not on module load. The reason is that the
 * READTHEDOCS_DATA might not be available during script load time.
 */
function get() {
    // Make `methods` the prototype.
    var config = Object.create(configMethods);

    var defaults = {
        api_host: 'https://readthedocs.org',
        ad_free: false,
    };

    $.extend(config, defaults, window.READTHEDOCS_DATA);

    return config;
}


module.exports = {
    get: get
};
