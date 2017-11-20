/* Documentation embed shared constants */

var exports = {
    THEME_RTD: 'sphinx_rtd_theme',
    THEME_ALABASTER: 'alabaster',
}

exports.PROMO_SUPPORTED_THEMES = [
    exports.THEME_RTD,
    exports.THEME_ALABASTER
]

exports.PROMO_TYPES = {
    LEFTNAV: 'doc',               // Left navigation on documentation pages
    FOOTER: 'site-footer'         // Footer of documentation pages
};

module.exports = exports;
