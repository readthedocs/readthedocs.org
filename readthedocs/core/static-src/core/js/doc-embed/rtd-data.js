/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */

var constants = require('./constants');

var configMethods = {
    is_rtd_theme: function () {
        return this.get_theme_name() === constants.THEME_RTD;
    },

    is_alabaster_theme: function () {
        // Returns true for Alabaster-like themes (eg. flask, celery)
        return this.get_theme_name() === constants.THEME_ALABASTER;
    },

    theme_supports_promo: function () {
        return constants.PROMO_SUPPORTED_THEMES.indexOf(this.get_theme_name()) > -1;
    },

    is_sphinx_builder: function () {
        return (!('builder' in this) || this.builder !== 'mkdocs');
    },

    is_mkdocs_builder: function () {
        return (!('builder' in this) || this.builder === 'mkdocs');
    },

    get_theme_name: function () {
        // Crappy heuristic, but people change the theme name on us.
        // So we have to do some duck typing.
        if (this.theme !== constants.THEME_RTD && this.theme !== constants.THEME_ALABASTER) {
            if (this.theme === constants.THEME_MKDOCS_RTD) {
                return constants.THEME_RTD;
            } else if ($('div.rst-other-versions').length === 1) {
                return constants.THEME_RTD;
            } else if ($('div.sphinxsidebar > div.sphinxsidebarwrapper').length === 1) {
                return constants.THEME_ALABASTER;
            }
        }
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
