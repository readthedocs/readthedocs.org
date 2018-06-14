/* Documentation embed shared constants */

var exports = {
    THEME_RTD: 'sphinx_rtd_theme',
    THEME_ALABASTER: 'alabaster',
    THEME_CELERY: 'sphinx_celery',
    THEME_MKDOCS_RTD: 'readthedocs',

    DEFAULT_PROMO_PRIORITY: 5,
    MINIMUM_PROMO_PRIORITY: 10,
    MAXIMUM_PROMO_PRIORITY: 1,
    LOW_PROMO_PRIORITY: 10,
};

exports.PROMO_SUPPORTED_THEMES = [
    exports.THEME_RTD,
    exports.THEME_ALABASTER,
    exports.THEME_CELERY
];

exports.PROMO_TYPES = {
    LEFTNAV: 'doc',                 // Left navigation on documentation pages
    FOOTER: 'site-footer',          // Footer of documentation pages
    FIXED_FOOTER: 'fixed-footer'    // A footer ad fixed at the bottom fo the screen
};

module.exports = exports;
