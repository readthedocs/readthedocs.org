/*
 * Sphinx search overrides.
 */

const rtddata = require('./rtd-data');
const { createDomNode, domReady } = require("./utils");
const MAX_RESULT_PER_SECTION = 3;
const MAX_SUBSTRING_LIMIT = 100;

/**
 * Mark a string as safe to be used as HTML in setNodeContent.
 * @class
 */
function SafeHtmlString(value) {
  this.value = value;
  this.isSafe = true;
}

/**
 * Create a SafeHtmlString instance from a string.
 *
 * @param {String} value
 */
function markAsSafe(value) {
  return new SafeHtmlString(value);
}

/**
 * Set the content of an element as text or HTML.
 *
 * @param {Element} element
 * @param {String|SafeHtmlString} content
 */
function setElementContent(element, content) {
  if (content.isSafe) {
    element.innerHTML = content.value;
  } else {
    element.innerText = content;
  }
}


/*
 * Search query override for hitting our local API instead of the standard
 * Sphinx indexer. This will fall back to the standard indexer on an API
 * failure.
 *
 * Except for highlights, which are HTML encoded, with `<span>` tags surrounding the highlight,
 * all other data shouldn't be considered safe to be used as HTML.
 */
function attach_elastic_search_query_sphinx(data) {
    var project = data.project;
    var version = data.version;
    var language = data.language || 'en';

    var query_override = function (query) {
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
         * @param {String|SafeHtmlString} title.
         * @param {String} link.
         * @param {String[]|SafeHtmlString[]} contents.
         */
        // Watch our for XSS in title and contents!
        const buildSection = function (title, link, contents) {
            var div_title = document.createElement("div");
            var a_element = document.createElement("a");
            a_element.href = link;
            setElementContent(a_element, title);

            div_title.appendChild(a_element);
            let elements = [div_title];
            for (let content of contents) {
                let div_content = document.createElement("div");
                setElementContent(div_content, content);
                elements.push(div_content);
            }
            return elements;
        };

        const clearProgressBar = function () {
            let progress = document.getElementById('search-progress');
            if (progress !== null) {
                progress.replaceChildren();
            }
            Search.stopPulse();
            setText(Search.title, _('Search Results'));
        };

        const doSearch = function (data) {
            var results = data.results || [];

            if (results.length) {
                for (var i = 0; i < results.length; i += 1) {
                    var result = results[i];
                    var blocks = result.blocks;
                    let list_item = createDomNode('li');

                    var title = result.title;
                    // if highlighted title is present, use that.
                    if (result.highlights.title.length) {
                        title = markAsSafe(result.highlights.title[0]);
                    }

                    var link = result.path + "?highlight=" + encodeURIComponent(query);

                    let item = createDomNode('a', {href: link});
                    setElementContent(item, title);
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
                                section_subtitle = markAsSafe(section.highlights.title[0]);
                            }

                            if (section.highlights.content.length) {
                                var content = section.highlights.content;
                                section_content = [];
                                for (
                                    var k = 0;
                                    k < content.length && k < MAX_RESULT_PER_SECTION;
                                    k += 1
                                ) {
                                    section_content.push(markAsSafe("... " + content[k] + " ..."));
                                }
                            }
                            let sections = buildSection(
                                section_subtitle,
                                section_subtitle_link,
                                section_content
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
            clearProgressBar();
        };

        const fallbackSearch = function () {
            console.debug('Read the Docs search failed. Falling back to Sphinx search.');
            Search.query_fallback(query);
            clearProgressBar();
        };

        fetch(search_url.href, {method: 'GET'})
        .then(response => {
            if (!response.ok) {
              throw new Error();
            }
            return response.json();
        })
        .then(data => {
            if (data.results.length > 0) {
                doSearch(data);
            } else {
                fallbackSearch();
            }
        })
        .catch(error => {
            fallbackSearch();
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
    domReady(function () {
        if (typeof Search !== 'undefined') {
            Search.init();
        }
    });
}


function init() {
    var data = rtddata.get();
    if (data.is_sphinx_builder()) {
        // Check to disabled server side search for Sphinx
        // happens inside the function, because we still need to call Search.init().
        attach_elastic_search_query_sphinx(data);
    } else {
        console.log('Server side search is disabled.');
    }
}

module.exports = {
    init: init
};
