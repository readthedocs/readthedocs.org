// Documentation build state

module.exports = {
    Build: Build
};

function Build (config) {
    this.config = config;

    // Crappy heuristic, but people change the theme name on us.  So we have to
    // do some duck typing.
    if (this.config['theme'] != 'sphinx_rtd_theme') {
        if ($('div.rst-other-versions').length == 1) {
            this.config['theme'] = 'sphinx_rtd_theme';
        }
    }

    if (this.config['api_host'] == undefined) {
        this.config['api_host'] = 'https://readthedocs.org';
    }
}

Build.prototype.is_rtd_theme = function () {
    return (this.config['theme'] == 'sphinx_rtd_theme');
};

Build.prototype.is_sphinx_builder = function () {
    return (!('builder' in this.config) || this.config['builder'] != 'mkdocs');
};

Build.prototype.show_promo = function () {
    return (this.config['api_host'] != 'https://readthedocs.com'
            && this.is_sphinx_builder()
            && this.is_rtd_theme());
};
