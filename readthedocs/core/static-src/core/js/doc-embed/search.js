/*
 * Sphinx search overrides
 */

var rtddata = require('./rtd-data'),
    xss = require('xss/lib/index');


function init() {
    var data = rtddata.get();
    attach_elastic_search_query(data);
}


/*
 * Search query override for hitting our local API instead of the standard
 * Sphinx indexer. This will fall back to the standard indexer on an API
 * failure,
 */
function attach_elastic_search_query(data) {
    var project = data.project,
        version = data.version,
        language = data.language || 'en',
        api_host = data.api_host;

    var query_override = function (query) {
        var search_def = $.Deferred(),
            search_url = document.createElement('a');

        search_url.href = api_host;
        search_url.pathname = '/api/v2/docsearch/';
        search_url.search = '?q=' + $.urlencode(query) + '&project=' + project +
            '&version=' + version + '&language=' + language;

        search_def
            .then(function (results) {
                var hits = results.hits || {},
                    hit_list = hits.hits || [];

                if (hit_list.length) {
                    for (var n in hit_list) {
                        var hit = hit_list[n],
                            fields = hit.fields || {},
                            list_item = $('<li style="display: none;"></li>'),
                            item_url = document.createElement('a'),
                            highlight = hit.highlight;

                        item_url.href += fields.link +
                            DOCUMENTATION_OPTIONS.FILE_SUFFIX;
                        item_url.search = '?highlight=' + $.urlencode(query);

                        // Result list elements
                        list_item.append(
                            $('<a />')
                            .attr('href', item_url)
                            .html(fields.title)
                        );
                        if (fields.project != project) {
                            list_item.append(
                                $('<span>')
                                .text(" (from project " + fields.project + ")")
                            );
                        }
                        if (highlight.content.length) {
                            var content = $('<div class="context">')
                                .html(xss(highlight.content[0]));
                            content.find('em').addClass('highlighted');
                            list_item.append(content);
                        }

                        Search.output.append(list_item);
                        list_item.slideDown(5);
                    }
                }

                if (!hit_list.length) {
                    // Fallback to Sphinx's indexes
                    Search.query_fallback(query);
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
            complete: function(resp, status_code) {
                if (typeof(resp.responseJSON) == 'undefined' ||
                        typeof(resp.responseJSON.results) == 'undefined') {
                    return search_def.reject();
                }
                return search_def.resolve(resp.responseJSON.results);
            }
        })
        .error(function (resp, status_code, error) {
            return search_def.reject();
        });
    };

    if (typeof Search !== 'undefined' && project && version) {
        var query_fallback = Search.query;
        Search.query_fallback = query_fallback;
        Search.query = query_override;
    }
    $(document).ready(function () {
        if (typeof Search !== 'undefined') {
            Search.init();
        }
    });
}

module.exports = {
    init: init
};
