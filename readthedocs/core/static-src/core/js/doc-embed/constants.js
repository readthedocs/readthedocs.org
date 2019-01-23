/* Documentation embed shared constants */

var exports = {
    THEME_RTD: 'sphinx_rtd_theme',
    THEME_ALABASTER: 'alabaster',
    THEME_MKDOCS_RTD: 'readthedocs',

    // Alabaster-like
    THEME_CELERY: 'sphinx_celery',
    THEME_BABEL: 'babel',
    THEME_CLICK: 'click',
    THEME_FLASK_SQLALCHEMY: 'flask-sqlalchemy',
    THEME_FLASK: 'flask',
    THEME_JINJA: 'jinja',
    THEME_PLATTER: 'platter',
    THEME_POCOO: 'pocoo',
    THEME_WERKZEUG: 'werkzeug',

    DEFAULT_PROMO_PRIORITY: 5,
    MINIMUM_PROMO_PRIORITY: 10,
    MAXIMUM_PROMO_PRIORITY: 1,
    LOW_PROMO_PRIORITY: 10,
};

exports.ALABASTER_LIKE_THEMES = [
    exports.THEME_ALABASTER,
    exports.THEME_CELERY,
    exports.THEME_BABEL,
    exports.THEME_CLICK,
    exports.THEME_FLASK_SQLALCHEMY,
    exports.THEME_FLASK,
    exports.THEME_JINJA,
    exports.THEME_PLATTER,
    exports.THEME_POCOO,
    exports.THEME_WERKZEUG,
];

exports.PROMO_TYPES = {
    LEFTNAV: 'doc',                 // Left navigation on documentation pages
    FOOTER: 'site-footer',          // Footer of documentation pages
    FIXED_FOOTER: 'fixed-footer'    // A footer ad fixed at the bottom fo the screen
};

module.exports = exports;
