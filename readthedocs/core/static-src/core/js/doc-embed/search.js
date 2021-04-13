/*
 * Sphinx and Mkdocs search overrides
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
        // this is the pre-1.7 syntax from Underscore.js
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
function attach_elastic_search_query_sphinx(data) {
    var project = data.project;
    var version = data.version;
    var language = data.language || 'en';

    var query_override = function (query) {
        var search_def = $.Deferred();
        var search_url = document.createElement('a');

        search_url.href = data.proxied_api_host + '/api/v2/search/';
        search_url.search = '?q=' + $.urlencode(query) + '&project=' + project +
                            '&version=' + version + '&language=' + language;

        search_def
            .then(function (data) {
                var results = data.results || [];

                if (results.length) {
                    for (var i = 0; i < results.length; i += 1) {
                        var result = results[i];
                        var blocks = result.blocks;
                        var list_item = $('<li style="display: none;"></li>');

                        var title = result.title;
                        // if highlighted title is present, use that.
                        if (result.highlights.title.length) {
                            title = xss(result.highlights.title[0]);
                        }

                        var link = result.path + "?highlight=" + $.urlencode(query);
                        // If we aren't on the main domain of the subproject, link to it.
                        // TODO: we should always redirect to the main domain instead.
                        if (result.path.startsWith('/projects/') && !window.location.href.startsWith(result.domain)) {
                            link = result.domain + link;
                        }

                        var item = $('<a>', {'href': link});

                        item.html(title);
                        item.find('span').addClass('highlighted');
                        list_item.append(item);

                        // If the document is from a subproject, add extra information
                        if (result.project !== project) {
                            var text = " (from project " + result.project_alias + ")";
                            var extra = $('<span>', {'text': text});
                            list_item.append(extra);
                        }

                        for (var block_index = 0; block_index < blocks.length; block_index += 1) {
                            var current_block = blocks[block_index];

                            var contents = $('<div class="context">');

                            var section_template =
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

                            var domain_template =
                                '<div>' +
                                    '<a href="<%= domain_subtitle_link %>">' +
                                        '<%= domain_subtitle %>' +
                                    '</a>' +
                                '</div>' +
                                '<div>' +
                                    '<%= domain_content %>' +
                                '</div>';

                            // if the result is page section
                            if (current_block.type === "section") {
                                var section = current_block;
                                var section_subtitle = section.title;
                                var section_subtitle_link = link + "#" + section.id;
                                var section_content = [section.content.substr(0, MAX_SUBSTRING_LIMIT) + " ..."];

                                if (section.highlights.title.length) {
                                    section_subtitle = xss(section.highlights.title[0]);
                                }

                                if (section.highlights.content.length) {
                                    var content = section.highlights.content;
                                    section_content = [];
                                    for (
                                        var k = 0;
                                        k < content.length && k < MAX_RESULT_PER_SECTION;
                                        k += 1
                                    ) {
                                        section_content.push("... " + xss(content[k]) + " ...");
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
                            if (current_block.type === "domain") {
                                var domain = current_block;
                                var domain_role_name = domain.role;
                                var domain_subtitle_link = link + "#" + domain.id;
                                var domain_name = domain.name;
                                var domain_content = "";

                                if (domain.content !== "") {
                                    domain_content = domain.content.substr(0, MAX_SUBSTRING_LIMIT) + " ...";
                                }

                                if (domain.highlights.content.length) {
                                    domain_content = "... " + xss(domain.highlights.content[0]) + " ...";
                                }

                                if (domain.highlights.name.length) {
                                    domain_name = xss(domain.highlights.name[0]);
                                }

                                var domain_subtitle = "[" + domain_role_name + "]: " + domain_name;

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
                            if (block_index < blocks.length - 1) {
                                list_item.append($("<div class='rtd_search_hits_spacing'></div>"));
                            }
                        }

                        Search.output.append(list_item);
                        list_item.slideDown(5);
                    }
                    Search.status.text(
                        _('Search finished, found %s page(s) matching the search query.').replace('%s', results.length)
                    );
                } else {
                    console.log('Read the Docs search failed. Falling back to Sphinx search.');
                    Search.query_fallback(query);
                }
            })
            .fail(function (error) {
                console.debug('Read the Docs search failed. Falling back to Sphinx search.');
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
        } else {
            console.log('Server side search is disabled.');
        }
    }
    $(document).ready(function () {
        if (typeof Search !== 'undefined') {
            Search.init();
        }
    });
}


/*
 * Mkdocs search override for hitting our API instead of the standard Mkdocs search index.
 * This will fall back to the original search on an API failure.
 */
function attach_elastic_search_query_mkdocs(data) {
    var project = data.project;
    var version = data.version;
    var language = data.language || 'en';

    var fallbackSearch = function () {
        if (typeof window.doSearchFallback !== 'undefined') {
            window.doSearchFallback();
        } else {
            console.log('Unable to fallback to original MkDocs search.');
        }
    };

    var doSearch = function () {
        var query = document.getElementById('mkdocs-search-query').value;

        var search_def = $.Deferred();

        var search_url = document.createElement('a');
        search_url.href = data.proxied_api_host + '/api/v2/search/';
        search_url.search = '?q=' + encodeURIComponent(query) + '&project=' + project +
                            '&version=' + version + '&language=' + language;

        search_def
            .then(function (data) {
                var results = data.results || [];

                if (results.length) {
                    var searchResults = $('#mkdocs-search-results');
                    searchResults.empty();

                    for (var i = 0; i < results.length; i += 1) {
                        var result = results[i];
                        var blocks = result.blocks;

                        var link = result.path;
                        // If we aren't on the main domain of the subproject, link to it.
                        // TODO: we should always redirect to the main domain instead.
                        if (result.path.startsWith('/projects/') && !window.location.href.startsWith(result.domain)) {
                            link = result.domain + link;
                        }

                        var item = $('<article>');
                        item.append(
                            $('<h3>').append($('<a>', {'href': link, 'text': result.title}))
                        );

                        if (result.project !== project) {
                            var text = '(from project ' + result.project_alias + ')';
                            item.append($('<span>', {'text': text}));
                        }

                        for (var j = 0; j < blocks.length; j += 1) {
                            var section = blocks[j];

                            if (section.type === 'section') {
                                var section_link = link + '#' + section.id;
                                var section_title = section.title;
                                var section_content = section.content;
                                if (section_content.length > MAX_SUBSTRING_LIMIT) {
                                    section_content = section_content.substr(0, MAX_SUBSTRING_LIMIT) + " ...";
                                }
                                var section_contents = [section_content];

                                if (section.highlights.title.length) {
                                    section_title = section.highlights.title[0];
                                }

                                if (section.highlights.content.length) {
                                    var contents = section.highlights.content;
                                    section_contents = [];
                                    for (
                                        var k = 0;
                                        k < contents.length && k < MAX_RESULT_PER_SECTION;
                                        k += 1
                                    ) {
                                        section_contents.push("... " + contents[k] + " ...");
                                    }
                                }

                                section_title = xss(section_title)
                                        .replace(/<span>/g, '<mark>')
                                        .replace(/<\/span>/g, '</mark>');
                                item.append(
                                    $('<h4>')
                                    .append($('<a>', {'href': section_link}).html(section_title))
                                );
                                for (var m = 0; m < section_contents.length; m += 1) {
                                    var content = xss(section_contents[m]);
                                    content = content
                                        .replace(/<span>/g, '<mark>')
                                        .replace(/<\/span>/g, '</mark>');
                                    item.append(
                                        $('<p>').html(content)
                                    );
                                }
                                searchResults.append(item);
                            }
                        }
                    }
                } else {
                    console.log('Read the Docs search returned 0 result. Falling back to MkDocs search.');
                    fallbackSearch();
                }
            })
            .fail(function (error) {
                console.log('Read the Docs search failed. Falling back to MkDocs search.');
                fallbackSearch();
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

    var initSearch = function () {
        var search_input = document.getElementById('mkdocs-search-query');
        if (search_input) {
            search_input.addEventListener('keyup', doSearch);
        }

        var term = window.getSearchTermFromLocation();
        if (term) {
            search_input.value = term;
            doSearch();
        }
    };

    $(document).ready(function () {
        // We can't override the search completely,
        // because we can't delete the original event listener,
        // and MkDocs includes its search functions after ours.
        // If MkDocs is loaded before, this will trigger a double search
        // (but ours will have precendece).

        // Note: this function is only available on Mkdocs >=1.x
        window.doSearchFallback = window.doSearch;

        window.doSearch = doSearch;
        window.initSearch = initSearch;
        initSearch();
    });
}


function init() {
    var data = rtddata.get();
    if (data.is_sphinx_builder()) {
        // Check to disabled server side search for Sphinx
        // happens inside the function, because we still need to call Search.init().
        attach_elastic_search_query_sphinx(data);
    }
    // MkDocs projects should have this flag explicitly for now.
    else if (data.features && !data.features.docsearch_disabled) {
        attach_elastic_search_query_mkdocs(data);
    } else {
        console.log('Server side search is disabled.');
    }
}

module.exports = {
    init: init
};
