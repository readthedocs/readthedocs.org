// For more details on analytics at Read the Docs, please see:
// https://docs.readthedocs.io/en/latest/advertising-details.html#analytics


// Skip analytics for users with Do Not Track enabled
if (navigator.doNotTrack === '1') {
    console.log('Respecting DNT with respect to analytics...');
} else {
    if (typeof READTHEDOCS_DATA !== 'undefined' && READTHEDOCS_DATA.global_analytics_code) {
        (function () {
            // New Google Site Tag (gtag.js) tagging/analytics framework
            // https://developers.google.com/gtagjs
            var script = document.createElement("script");
            script.src = "https://www.googletagmanager.com/gtag/js?id=" + READTHEDOCS_DATA.global_analytics_code;
            script.type = "text/javascript";
            script.async = true;
            document.getElementsByTagName("head")[0].appendChild(script);
        }())

        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        // Setup the RTD global analytics code and send a pageview
        gtag('config', READTHEDOCS_DATA.global_analytics_code, {
            'anonymize_ip': true,
            'cookie_expires': 30 * 24 * 60 * 60,  // 30 days
            'dimension1': READTHEDOCS_DATA.project,
            'dimension2': READTHEDOCS_DATA.version,
            'dimension3': READTHEDOCS_DATA.language,
            'dimension4': READTHEDOCS_DATA.theme,
            'dimension5': READTHEDOCS_DATA.programming_language,
            'dimension6': READTHEDOCS_DATA.builder,
            'groups': 'rtfd'
        });

        // Setup the project (user) analytics code and send a pageview
        if (READTHEDOCS_DATA.user_analytics_code) {
            gtag('config', READTHEDOCS_DATA.user_analytics_code, {
                'anonymize_ip': true,
                'cookie_expires': 30 * 24 * 60 * 60  // 30 days
            });
        }
    }
    // end RTD Analytics Code
}
