/*
 * Allow highlighting of search terms, passed in as "highlight" GET parameter.
 *
 * This imitades the behaviour of what is implemented in Sphinx's doctools.js.
 * Mkdocs does not provide a similiar logic, we implement it here instead which
 * will work theme agnostic.
 */


require('./jquery.highlighttext');


function init() {
    highlightSearchWords();
}


function urldecode(x) {
    return decodeURIComponent(x).replace(/\+/g, ' ');
}


function getQueryParameters(s) {
    if (typeof s == 'undefined')
        s = document.location.search;
    var parts = s.substr(s.indexOf('?') + 1).split('&');
    var result = {};
    for (var i = 0; i < parts.length; i++) {
        var tmp = parts[i].split('=', 2);
        var key = urldecode(tmp[0]);
        var value = urldecode(tmp[1]);
        if (key in result)
            result[key].push(value);
        else
            result[key] = [value];
    }
    return result;
}


function highlightSearchWords() {
    var params = getQueryParameters();
    var terms = (params.highlight) ? params.highlight[0].split(/\s+/) : [];
    if (terms.length) {
        var body = $('div.body');
        if (!body.length) {
            var body = $('body');
        }
        window.setTimeout(function() {
            $.each(terms, function() {
                body.highlightText(this.toLowerCase(), 'highlighted');
            });
        }, 10);
    }
}


module.exports = {
    init: init
};
