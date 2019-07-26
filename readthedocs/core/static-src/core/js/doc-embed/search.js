/*
 * Sphinx search overrides
 */

var rtddata = require('./rtd-data');
var xss = require('xss/lib/index');
var MAX_RESULT_PER_SECTION = 3;
var MAX_SUBSTRING_LIMIT = 100;

/**
 * Use try...catch block to append html to contents
 *
 * @param {Object} contents html element on which additional html is be appended
 * @param {String} template underscore.js template string
 * @param {Object} data template vars and their values
 */
function append_html_to_contents(contents, template, data) {
    // underscore.js throws variable not defined error
    // because of change of syntax in new versions.
    // See: https://stackoverflow.com/a/25881231/8601393
    try {
        // this is the old syntax
        contents.append(
            $u.template(
                template,
                data
            )
        );
    }
    catch (error) {
        // this is the new syntax
        contents.append(
            $u.template(template)(data)
        );
    }
}

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
                        var inner_hits = doc.inner_hits || [];
                        var list_item = $('<li style="display: none;"></li>');

                        var title = doc.title;
                        // if highlighted title is present,
                        // use that.
                        if (highlight) {
                            if (highlight.title) {
                                title = xss(highlight.title[0]);
                            }
                        }

                        // Creating the result from elements
                        var link = doc.link + DOCUMENTATION_OPTIONS.FILE_SUFFIX + "?highlight=" + $.urlencode(query);

                        var item = $('<a>', {'href': link});
                        item.html(title);
                        item.find('span').addClass('highlighted');
                        list_item.append(item);

                        // If the document is from subproject, add extra information
                        if (doc.project !== project) {
                            var text = " (from project " + doc.project + ")";
                            var extra = $('<span>', {'text': text});

                            list_item.append(extra);
                        }

                        for (var j = 0; j < inner_hits.length; j += 1) {

                            var contents = $('<div class="context">');

                            var section = "";
                            var section_subtitle = "";
                            var section_subtitle_link = "";
                            var section_content = "";
                            var content = "";

                            var domain = "";
                            var domain_subtitle = "";
                            var domain_subtitle_link = "";
                            var domain_content = "";
                            var domain_name = "";

                            var section_template = '' +
                                '<div>' +
                                    '<a href="<%= section_subtitle_link %>">' +
                                        '<%= section_subtitle %>' +
                                    '</a>' +
                                '</div>' +
                                '<% for (var i = 0; i < section_content.length; ++i) { %>' +
                                    '<div>' +
                                        '<%= section_content[i] %>' +
                                    '</div>' +
                                '<% } %>';

                            var domain_template = '' +
                                '<div>' +
                                    '<a href="<%= domain_subtitle_link %>">' +
                                        '<%= domain_subtitle %>' +
                                    '</a>' +
                                '</div>' +
                                '<div>' +
                                    '<%= domain_content %>' +
                                '</div>';

                            // if the result is page section
                            if(inner_hits[j].type === "sections") {

                                section = inner_hits[j];
                                section_subtitle = section._source.title;
                                section_subtitle_link = link + "#" + section._source.id;
                                section_content = [section._source.content.substring(0, MAX_SUBSTRING_LIMIT) + " ..."];

                                if (section.highlight) {
                                    if (section.highlight["sections.title"]) {
                                        section_subtitle = xss(section.highlight["sections.title"][0]);
                                    }

                                    if (section.highlight["sections.content"]) {
                                        content = section.highlight["sections.content"];
                                        section_content = [];
                                        for (
                                            var k = 0;
                                            k < content.length && k < MAX_RESULT_PER_SECTION;
                                             k += 1
                                        ) {
                                            section_content.push("... " + xss(content[k]) + " ...");
                                        }
                                    }
                                }

                                append_html_to_contents(
                                    contents,
                                    section_template,
                                    {
                                        section_subtitle_link: section_subtitle_link,
                                        section_subtitle: section_subtitle,
                                        section_content: section_content
                                    }
                                );
                            }

                            // if the result is a sphinx domain object
                            if (inner_hits[j].type === "domains") {

                                domain = inner_hits[j];
                                domain_subtitle = domain._source.role_name;
                                domain_subtitle_link = link + "#" + domain._source.anchor;
                                domain_content = "";
                                domain_name = domain._source.name;

                                if (
                                    typeof domain._source.display_name === "string" &&
                                    domain._source.display_name.length >= 1
                                ) {
                                    domain_subtitle = "(" + domain._source.role_name + ") " + domain._source.display_name;
                                }

                                if (domain.highlight) {
                                    if (domain.highlight["domains.name"]) {
                                        // domain_content = type_display -- name
                                        domain_name = xss(domain.highlight["domains.name"][0]);
                                    }
                                }

                                // domain_content = type_display -- name -- in doc_display
                                domain_content = domain._source.type_display + " -- " + domain_name + " -- in " + domain._source.doc_display;

                                append_html_to_contents(
                                    contents,
                                    domain_template,
                                    {
                                        domain_subtitle_link: domain_subtitle_link,
                                        domain_subtitle: domain_subtitle,
                                        domain_content: domain_content
                                    }
                                );
                            }

                            contents.find('span').addClass('highlighted');
                            list_item.append(contents);

                            // Create some spacing between the results.
                            // Also, don't add this spacing in the last hit.
                            if (j !== inner_hits.length - 1) {
                                list_item.append($("<div class='rtd_search_hits_spacing'></div>"));
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
