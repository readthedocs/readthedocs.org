// For more details on analytics at Read the Docs, please see:
// https://docs.readthedocs.io/en/latest/advertising-details.html#analytics


// Skip analytics for users with Do Not Track enabled
if (navigator.doNotTrack === '1') {
    console.log('Respecting DNT with respect to analytics...');
} else {
    if (typeof READTHEDOCS_DATA !== 'undefined' && READTHEDOCS_DATA.global_analytics_code) {
        // RTD Analytics Code
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

        ga('create', READTHEDOCS_DATA.global_analytics_code, 'auto', 'rtfd', {
          'cookieExpires': 30 * 24 * 60 * 60
        });
        ga('rtfd.set', 'dimension1', READTHEDOCS_DATA.project);
        ga('rtfd.set', 'dimension2', READTHEDOCS_DATA.version);
        ga('rtfd.set', 'dimension3', READTHEDOCS_DATA.language);
        ga('rtfd.set', 'dimension4', READTHEDOCS_DATA.theme);
        ga('rtfd.set', 'dimension5', READTHEDOCS_DATA.programming_language);
        ga('rtfd.set', 'dimension6', READTHEDOCS_DATA.builder);
        ga('rtfd.set', 'anonymizeIp', true);
        ga('rtfd.send', 'pageview');

        // User Analytics Code
        if (READTHEDOCS_DATA.user_analytics_code) {
            ga('create', READTHEDOCS_DATA.user_analytics_code, 'auto', 'user', {
              'cookieExpires': 30 * 24 * 60 * 60
            });
            ga('user.set', 'anonymizeIp', true);
            ga('user.send', 'pageview');
        }
        // End User Analytics Code
    }
    // end RTD Analytics Code
}
