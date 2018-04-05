// Google Analytics is a contentious issue inside Read the Docs and in our community.
// Some users are very sensitive and privacy conscious to usage of GA.
// Other users want their own GA tracker on their docs to see the usage their docs get.
// The developers at Read the Docs understand that different users have different priorities
// and we try to respect the different viewpoints as much as possible while also accomplishing
// our own goals.

// Read the Docs largely funds our operations and development through advertising and
// advertisers ask us questions that are easily answered with an analytics solution like
// "how many users do you have in Switzerland browsing Python docs?". We need to be able
// to easily get this data. We also use data from GA for some development decisions such
// as what browsers to support (or not) or how much usage a particular page/feature gets.

// We have taken steps with GA to address some of the privacy issues.
// Read the Docs instructs Google to anonymize IPs sent to them before they are stored (see below).

// We are always exploring our options with respect to analytics and if you would like
// to discuss further, feel free to open an issue on github.


// RTD Analytics Code

(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

if (typeof READTHEDOCS_DATA !== 'undefined') {
    if (READTHEDOCS_DATA.global_analytics_code) {
        ga('create', READTHEDOCS_DATA.global_analytics_code, 'auto', 'rtfd');
        ga('rtfd.set', 'dimension1', READTHEDOCS_DATA.project);
        ga('rtfd.set', 'dimension2', READTHEDOCS_DATA.version);
        ga('rtfd.set', 'dimension3', READTHEDOCS_DATA.language);
        ga('rtfd.set', 'dimension4', READTHEDOCS_DATA.theme);
        ga('rtfd.set', 'dimension5', READTHEDOCS_DATA.programming_language);
        ga('rtfd.set', 'dimension6', READTHEDOCS_DATA.builder);
        ga('rtfd.set', 'anonymizeIp', true);
        ga('rtfd.send', 'pageview');
    }

    // User Analytics Code
    if (READTHEDOCS_DATA.user_analytics_code) {
        ga('create', READTHEDOCS_DATA.user_analytics_code, 'auto', 'user');
        ga('user.set', 'anonymizeIp', true);
        ga('user.send', 'pageview');
    }
    // End User Analytics Code
}

// end RTD Analytics Code
