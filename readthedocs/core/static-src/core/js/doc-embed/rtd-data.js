/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */


var configMethods = {
    is_rtd_theme: function () {
        return this.get_theme_name() === 'sphinx_rtd_theme';
    },

    is_sphinx_builder: function () {
        return (!('builder' in this) || this.builder != 'mkdocs');
    },

    get_theme_name: function () {
        // Crappy heuristic, but people change the theme name on us.  So we have to
        // do some duck typing.
        if (this.theme !== 'sphinx_rtd_theme') {
            if ($('div.rst-other-versions').length === 1) {
                return 'sphinx_rtd_theme';
            }
        }
        return this.theme;
    },

    show_promo: function () {
        return (
            this.api_host !== 'https://readthedocs.com' &&
            this.is_sphinx_builder() &&
            this.is_rtd_theme());
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
        api_host: 'https://readthedocs.org'
    };

    $.extend(config, defaults, window.READTHEDOCS_DATA);

    return config;
}


module.exports = {
    get: get
};
