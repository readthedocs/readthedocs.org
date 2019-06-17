/*
 * Sphinx search overrides
 */

var rtddata = require('./rtd-data');
var xss = require('xss/lib/index');


/*
 * Search query override for hitting our local API instead of the standard
 * Sphinx indexer. This will fall back to the standard indexer on an API
 * failure,
 */
function attach_elastic_search_query(data) {
    var project = data.project;
    var version = data.version;
    var language = data.language || 'en';
    var api_host = data.api_host;

    var query_override = function (query) {
        var search_def = $.Deferred();
        var search_url = document.createElement('a');

        search_url.href = api_host;
        search_url.pathname = '/api/v2/docsearch/';
        search_url.search = '?q=' + $.urlencode(query) + '&project=' + project +
                            '&version=' + version + '&language=' + language;

        search_def
            .then(function (data) {
                var hit_list = data.results || [];
                var total_count = data.count || 0;

                if (hit_list.length) {
                    for (var i = 0; i < hit_list.length; i += 1) {
                        var doc = hit_list[i];
                        var highlight = doc.highlight;
                        var list_item = $('<li style="display: none;"></li>');

                        // Creating the result from elements
                        var url = doc.url + '?highlight=' + $.urlencode(query);

                        var item = $('<a>', {'href': url});
                        item.html(doc.title);
                        list_item.append(item);

                        // If the document is from subproject, add extra information
                        if (doc.project !== project) {
                            var text = " (from project " + doc.project + ")";
                            var extra = $('<span>', {'text': text});

                            list_item.append(extra);
                        }

                        // Show highlighted texts
                        if (highlight.content) {
                            for (var index = 0; index < highlight.content.length; index += 1) {
                                if (index < 3) {
                                    // Show up to 3 results for search
                                    var content = highlight.content[index];
                                    var content_text = xss(content);
                                    var contents = $('<div class="context">');

                                    contents.html("..." + content_text + "...");
                                    contents.find('em').addClass('highlighted');
                                    list_item.append(contents);
                                }
                            }
                        }

                        Search.output.append(list_item);
                        list_item.slideDown(5);
                    }
                }

                if (!hit_list.length) {
                    // Fallback to Sphinx's indexes
                    Search.query_fallback(query);
                    console.log('Read the Docs search failed. Falling back to Sphinx search.');
                }
                else {
                    Search.status.text(
                        _('Search finished, found %s page(s) matching the search query.').replace('%s', hit_list.length)
                    );
                }
            })
            .fail(function (error) {
                // Fallback to Sphinx's indexes
                Search.query_fallback(query);
            })
            .always(function () {
                $('#search-progress').empty();
                Search.stopPulse();
                Search.title.text(_('Search Results'));
                Search.status.fadeIn(500);
            });

        $.ajax({
            url: search_url.href,
            crossDomain: true,
            xhrFields: {
                withCredentials: true,
            },
            complete: function (resp, status_code) {
                if (
                    status_code !== 'success' ||
                    typeof (resp.responseJSON) === 'undefined' ||
                    resp.responseJSON.count === 0
                ) {
                    return search_def.reject();
                }
                return search_def.resolve(resp.responseJSON);
            }
        })
        .fail(function (resp, status_code, error) {
            return search_def.reject();
        });
    };

    if (typeof Search !== 'undefined' && project && version) {

        // Do not replace the built-in search if RTD's docsearch is disabled
        if (!data.features || !data.features.docsearch_disabled) {
            var query_fallback = Search.query;
            Search.query_fallback = query_fallback;
            Search.query = query_override;
        }
    }
    $(document).ready(function () {
        if (typeof Search !== 'undefined') {
            Search.init();
        }
    });
}


function init() {
    var data = rtddata.get();
    attach_elastic_search_query(data);
}

module.exports = {
    init: init
};
