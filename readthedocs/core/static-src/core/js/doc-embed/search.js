/*
 * Sphinx and Mkdocs search overrides
 */

var rtddata = require('./rtd-data');
var xss = require('xss/lib/index');
var MAX_RESULT_PER_SECTION = 3;
var MAX_SUBSTRING_LIMIT = 100;

/**
 * Create and return DOM nodes with given attributes.
 *
 * @param {String} nodeName name of the node
 * @param {Object} attributes obj of attributes to be assigned to the node
 * @return {Object} DOM node
 */
const createDomNode = (nodeName, attributes) => {
    let node = document.createElement(nodeName);
    if (attributes) {
        for (let attr of Object.keys(attributes)) {
            node.setAttribute(attr, attributes[attr]);
        }
    }
    return node;
};


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
        search_url.search = '?q=' + encodeURIComponent(query) + '&project=' + project +
                            '&version=' + version + '&language=' + language;

        /*
         * Compatibility function to set a text to a Node or JQuery object.
         */
        var setText = function (node, text) {
          if (node.jquery) {
            node.text(text);
          } else {
            node.innerText = text;
          }
        };

        /**
         * Build a section with its matching results.
         *
         * A section has the form:
         *
         *   <div>
         *     <a href={link}>{title}<a>
         *   </div>
         *   <div>
         *     {contents[0]}
         *   </div>
         *   <div>
         *     {contents[1]}
         *   </div>
         *
         *   ...
         *
         * @param {String} title.
         * @param {String} link.
         * @param {Array} contents.
         */
        const buildSection = function (title, link, contents) {
            var div_title = document.createElement("div");
            var a_element = document.createElement("a");
            a_element.href = link;
            a_element.innerHTML = title;
            div_title.appendChild(a_element);
            let elements = [div_title];
            for (let content of contents) {
                let div_content = document.createElement("div");
                div_content.innerHTML = content;
                elements.push(div_content);
            }
            return elements;
        };

        search_def
            .then(function (data) {
                var results = data.results || [];

                if (results.length) {
                    for (var i = 0; i < results.length; i += 1) {
                        var result = results[i];
                        var blocks = result.blocks;
                        let list_item = createDomNode('li');

                        var title = result.title;
                        // if highlighted title is present, use that.
                        if (result.highlights.title.length) {
                            title = xss(result.highlights.title[0]);
                        }

                        var link = result.path + "?highlight=" + encodeURIComponent(query);

                        let item = createDomNode('a', {href: link});
                        item.innerHTML = title;
                        for (let element of item.getElementsByTagName('span')) {
                            element.className = 'highlighted';
                        }
                        list_item.appendChild(item);

                        // If the document is from a subproject, add extra information
                        if (result.project !== project) {
                            let extra = createDomNode('span');
                            extra.innerText = " (from project " + result.project_alias + ")";
                            list_item.appendChild(extra);
                        }

                        for (var block_index = 0; block_index < blocks.length; block_index += 1) {
                            var current_block = blocks[block_index];

                            let contents = createDomNode('div', {class: 'context'});

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
                                let sections = buildSection(
                                    section_subtitle,
                                    section_subtitle_link,
                                    section_content
                                );
                                sections.forEach(element => { contents.appendChild(element); });
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

                                let sections = buildSection(
                                    domain_subtitle,
                                    domain_subtitle_link,
                                    [domain_content]
                                );
                                sections.forEach(element => { contents.appendChild(element); });
                            }

                            for (let element of contents.getElementsByTagName('span')) {
                                element.className = 'highlighted';
                            }
                            list_item.appendChild(contents);

                            // Create some spacing between the results.
                            // Also, don't add this spacing in the last hit.
                            if (block_index < blocks.length - 1) {
                                list_item.appendChild(createDomNode('div', {class: 'rtd_search_hits_spacing'}));
                            }
                        }

                        if (Search.output.jquery) {
                          Search.output.append($(list_item));
                        } else {
                          Search.output.appendChild(list_item);
                        }
                    }
                    setText(
                        Search.status,
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
                let progress = document.getElementById('search-progress');
                if (progress !== null) {
                  progress.replaceChildren();
                }
                Search.stopPulse();
                setText(Search.title, _('Search Results'));
            });

        fetch(search_url.href, {method: 'GET'})
        .then(response => {
            if (!response.ok) {
              throw new Error();
            }
            return response.json();
        })
        .then(data => {
            if (data.results.length > 0) {
                search_def.resolve(data);
            } else {
                search_def.reject();
            }
        })
        .catch(error => {
            search_def.reject();
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
                    let searchResults = document.getElementById('mkdocs-search-results');
                    if (searchResults != null) {
                        searchResults.replaceChildren();
                    }

                    for (var i = 0; i < results.length; i += 1) {
                        var result = results[i];
                        var blocks = result.blocks;

                        var link = result.path;

                        let item = createDomNode('article');
                        let a_element = createDomNode('a', {href: link});
                        a_element.innerText = result.title;
                        let title_element = createDomNode('h3');
                        title_element.appendChild(a_element);
                        item.appendChild(title_element);

                        if (result.project !== project) {
                            let text = '(from project ' + result.project_alias + ')';
                            item.appendChild(createDomNode('span', {'text': text}));
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

                                let title_element = createDomNode('h4');
                                let a_element = createDomNode('a', {href: section_link});
                                a_element.innerHTML = section_title;
                                title_element.appendChild(a_element);
                                item.appendChild(title_element);

                                for (var m = 0; m < section_contents.length; m += 1) {
                                    let content = xss(section_contents[m]);
                                    content = content
                                        .replace(/<span>/g, '<mark>')
                                        .replace(/<\/span>/g, '</mark>');
                                    let p_element = createDomNode('p');
                                    p_element.innerHTML = content;
                                    item.appendChild(p_element);
                                }
                                searchResults.appendChild(item);
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

        fetch(search_url.href, {method: 'GET'})
        .then(response => {
            if (!response.ok) {
                throw new Error();
            }
            return response.json();
        })
        .then(data => {
            if (data.results.length > 0) {
                search_def.resolve(data);
            } else {
                search_def.reject();
            }
        })
        .catch(error => {
            search_def.reject();
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
