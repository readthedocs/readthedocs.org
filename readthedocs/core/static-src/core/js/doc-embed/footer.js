var rtddata = require('./rtd-data'),
    versionCompare = require('./version-compare'),
    sponsorship = require('../sponsorship');


function init() {
    var rtd = rtddata.get();

    var get_data = {
        project: rtd['project'],
        version: rtd['version'],
        page: rtd['page'],
        theme: rtd.get_theme_name(),
        format: "jsonp",
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
    $.ajax({
        url: rtd.api_host + "/api/v2/footer_html/",
        crossDomain: true,
        xhrFields: {
            withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
            versionCompare.init(data.version_compare);
            injectFooter(data);
            setupBookmarkCSRFToken();
        },
        error: function () {
            console.error('Error loading Read the Docs footer');
        }
    });
}


function injectFooter(data) {
    var config = rtddata.get();

    // If the theme looks like ours, update the existing badge
    // otherwise throw a a full one into the page.
    if (config.is_rtd_theme()) {
        $("div.rst-other-versions").html(data['html']);
    } else {
        $("body").append(data['html']);
    }

    if (!data['version_active']) {
        $('.rst-current-version').addClass('rst-out-of-date');
    } else if (!data['version_supported']) {
        //$('.rst-current-version').addClass('rst-active-old-version')
    }

    // Show promo selectively
    if (data.promo && config.show_promo()) {
        var promo = new sponsorship.Promo(
            data.promo_data.id,
            data.promo_data.text,
            data.promo_data.link,
            data.promo_data.image
        )
        if (promo) {
            promo.display();
        }
    }
}


function setupBookmarkCSRFToken() {
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", $('a.bookmark[token]').attr('token'));
            }
        }
    });
}


module.exports = {
    init: init
};
