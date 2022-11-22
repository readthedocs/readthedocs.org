var rtddata = require('./rtd-data');
var versionCompare = require('./version-compare');

var EXPLICIT_FLYOUT_PLACEMENT_SELECTOR = '#readthedocs-embed-flyout';


function injectFooter(data) {
    // Injects the footer into the page
    // There are 3 main cases:
    // * EXPLICIT_FLYOUT_PLACEMENT_SELECTOR is defined, inject it there
    // * The page looks like our Sphinx theme, updated the existing div
    // * All other pages just get it appended to the <body>

    var config = rtddata.get();
    let placement = document.querySelector(EXPLICIT_FLYOUT_PLACEMENT_SELECTOR);
    if (placement !== null) {
        placement.innerHTML = data['html'];
    }
    else if (config.is_sphinx_builder() && config.is_rtd_like_theme()) {
        let placement = document.querySelector('div.rst-other-versions');
        if (placement !== null) {
            placement.innerHTML = data['html'];
        }
    } else {
        document.body.insertAdjacentHTML('beforeend', data['html']);
    }

    if (!data['version_active']) {
      for (let element of document.getElementsByClassName('rst-current-version')) {
          element.classList.add('rst-out-of-date');
      }
    } else if (!data['version_supported']) {
        //$('.rst-current-version').addClass('rst-active-old-version')
    }
}


function init() {
    var rtd = rtddata.get();

    var get_data = {
        project: rtd['project'],
        version: rtd['version'],
        // Page is a sphinx concept only,
        // avoid serializing this as a literal `null` instead of empty.
        page: rtd['page'] || "",
        theme: rtd.get_theme_name(),
    };

    // Crappy heuristic, but people change the theme name on us.
    // So we have to do some duck typing.
    if ("docroot" in rtd) {
        get_data['docroot'] = rtd['docroot'];
    }

    if ("source_suffix" in rtd) {
        get_data['source_suffix'] = rtd['source_suffix'];
    }

    if (window.location.pathname.indexOf('/projects/') === 0) {
        get_data['subproject'] = true;
    }

    // Get footer HTML from API and inject it into the page.
    let footer_api_url = rtd.proxied_api_host + "/api/v2/footer_html/?" + new URLSearchParams(get_data).toString();
    fetch(footer_api_url, {method: 'GET'})
    .then(response => {
        if (!response.ok) {
            throw new Error();
        }
        return response.json();
    })
    .then(data => {
        if (data.show_version_warning) {
            versionCompare.init(data.version_compare);
        }
        injectFooter(data);
    })
    .catch(error => {
        console.error('Error loading Read the Docs footer');
    });

    // Register page view.
    let data = {
        project: rtd['project'],
        version: rtd['version'],
        absolute_uri: window.location.href,
    };
    let url = rtd.proxied_api_host + '/api/v2/analytics/?' + new URLSearchParams(data).toString();
    fetch(url, {method: 'GET', cache: 'no-store'})
    .then(response => {
        if (!response.ok) {
            throw new Error();
        }
    })
    .catch(error => {
        console.error('Error registering page view');
    });
}

module.exports = {
    init: init
};
