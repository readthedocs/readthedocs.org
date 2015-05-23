(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
// Documentation build state

module.exports = {
    Build: Build
};

function Build (config) {
    this.config = config;

    // Crappy heuristic, but people change the theme name on us.  So we have to
    // do some duck typing.
    if (this.config['theme'] != 'sphinx_rtd_theme') {
        if ($('div.rst-other-versions').length == 1) {
            this.config['theme'] = 'sphinx_rtd_theme';
        }
    }

    if (this.config['api_host'] == undefined) {
        this.config['api_host'] = 'https://readthedocs.org';
    }
}

Build.prototype.is_rtd_theme = function () {
    return (this.config['theme'] == 'sphinx_rtd_theme');
};

Build.prototype.is_sphinx_builder = function () {
    return (!('builder' in this.config) || this.config['builder'] != 'mkdocs');
};

Build.prototype.show_promo = function () {
    return (this.config['api_host'] != 'https://readthedocs.com'
            && this.is_sphinx_builder()
            && this.is_rtd_theme());
};

},{}],2:[function(require,module,exports){
var sponsorship = require('./sponsorship'),
    doc = require('./doc');

$(document).ready(function () {

    var build = new doc.Build(READTHEDOCS_DATA);

    get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        page: READTHEDOCS_DATA['page'],
        theme: READTHEDOCS_DATA['theme'],
        format: "jsonp",
    };


    // Crappy heuristic, but people change the theme name on us.
    // So we have to do some duck typing.
    if ("docroot" in READTHEDOCS_DATA) {
      get_data['docroot'] = READTHEDOCS_DATA['docroot'];
    }

    if ("source_suffix" in READTHEDOCS_DATA) {
      get_data['source_suffix'] = READTHEDOCS_DATA['source_suffix'];
    }

    var API_HOST = READTHEDOCS_DATA['api_host'];
    if (API_HOST === undefined) {
      API_HOST = 'https://readthedocs.org';
    }

    if (window.location.pathname.indexOf('/projects/') === 0) {
      get_data['subproject'] = true;
    }

    // Theme popout code
    $.ajax({
      url: API_HOST + "/api/v2/footer_html/",
      crossDomain: true,
      xhrFields: {
        withCredentials: true,
      },
      dataType: "jsonp",
      data: get_data,
      success: function (data) {
            // If the theme looks like ours, update the existing badge
            // otherwise throw a a full one into the page.
            if (build.is_rtd_theme()) {
              $("div.rst-other-versions").html(data['html']);
            } else {
              $("body").append(data['html']);
            }

            if (!data['version_active']) {
                $('.rst-current-version').addClass('rst-out-of-date');
            } else if (!data['version_supported']) {
                //$('.rst-current-version').addClass('rst-active-old-version')
            }

            // Show promo selectively
            if (data.promo && build.show_promo()) {
                // TODO don't hardcode this promo
                var promo = sponsorship.Promo.from_variants([
                    /*
                    {
                        id: '',
                        text: 'Example <a>linked</a> text',
                        link: '',
                        image: ''
                    }
                    */
                ]);
                if (promo) {
                    promo.display();
                }
            }

            // using jQuery
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

              function csrfSafeMethod(method) {
                  // these HTTP methods do not require CSRF protection
                  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
              }
              $.ajaxSetup({
                  beforeSend: function(xhr, settings) {
                      if (!csrfSafeMethod(settings.type)) {
                          xhr.setRequestHeader("X-CSRFToken", $('a.bookmark[token]').attr('token'));
                      }
                  }
              });

            // Bookmark Handling
            data = {
                project: READTHEDOCS_DATA['project'],
                version: READTHEDOCS_DATA['version'],
                page: READTHEDOCS_DATA['page'],
                url: document.location.origin + document.location.pathname
            };

            // ask the server if a bookmark exists for this page so we can show the proper icon
            $.ajax({
                    type: 'POST',
                    url: API_HOST + "/bookmarks/exists/",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    data: JSON.stringify(data),
                    success: function (data) {
                      $(".bookmark-active").show();
                    },
                    error: function(data) {
                      $(".bookmark-inactive").show();
                    },
                    dataType: 'json'
            });

            $(".bookmark-icon").on('click', function (event) {
              var bookmarked = $('.bookmark-active').is(':visible');
              $('div.bookmark-active').toggle();
              $('div.bookmark-inactive').toggle();

              if (bookmarked) {
                  $.ajax({
                    type: "POST",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    url: API_HOST + "/bookmarks/remove/",
                    data: JSON.stringify(data),
                    });
                  //$(".bookmark-added-msg").hide();
              } else {
                  $.ajax({
                    type: "POST",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    url: API_HOST + "/bookmarks/add/",
                    data: JSON.stringify(data),
                    });
                    //$(".bookmark-added-msg").html("<p><a href='/bookmarks'>Bookmark</a> added</p>");
                    //$(".bookmark-added-msg").show();
              }
            });
      },
      error: function () {
          console.log('Error loading Read the Docs footer');
      }
    });


    /// Read the Docs Sphinx theme code
    if (!("builder" in READTHEDOCS_DATA) || "builder" in READTHEDOCS_DATA && READTHEDOCS_DATA["builder"] != "mkdocs") {
        function toggleCurrent (elem) {
            var parent_li = elem.closest('li');
            parent_li.siblings('li.current').removeClass('current');
            parent_li.siblings().find('li.current').removeClass('current');
            parent_li.find('> ul li.current').removeClass('current');
            parent_li.toggleClass('current');
        }

        // Shift nav in mobile when clicking the menu.
        $(document).on('click', "[data-toggle='wy-nav-top']", function() {
            $("[data-toggle='wy-nav-shift']").toggleClass("shift");
            $("[data-toggle='rst-versions']").toggleClass("shift");
        });
        // Nav menu link click operations
        $(document).on('click', ".wy-menu-vertical .current ul li a", function() {
            var target = $(this);
            // Close menu when you click a link.
            $("[data-toggle='wy-nav-shift']").removeClass("shift");
            $("[data-toggle='rst-versions']").toggleClass("shift");
            // Handle dynamic display of l3 and l4 nav lists
            toggleCurrent(target);
            if (typeof(window.SphinxRtdTheme) != 'undefined') {
                window.SphinxRtdTheme.StickyNav.hashChange();
            }
        });
        $(document).on('click', "[data-toggle='rst-current-version']", function() {
            $("[data-toggle='rst-versions']").toggleClass("shift-up");
        });
        // Make tables responsive
        $("table.docutils:not(.field-list)").wrap("<div class='wy-table-responsive'></div>");

        // Add expand links to all parents of nested ul
        $('.wy-menu-vertical ul').siblings('a').each(function () {
            var link = $(this);
                expand = $('<span class="toctree-expand"></span>');
            expand.on('click', function (ev) {
                toggleCurrent(link);
                ev.stopPropagation();
                return false;
            });
            link.prepend(expand);
        });

        // Sphinx theme state
        window.SphinxRtdTheme = (function (jquery) {
            var stickyNav = (function () {
                var navBar,
                    win,
                    winScroll = false,
                    linkScroll = false,
                    winPosition = 0,
                    enable = function () {
                        init();
                        reset();
                        win.on('hashchange', reset);

                        // Set scrolling
                        win.on('scroll', function () {
                            if (!linkScroll) {
                                winScroll = true;
                            }
                        });
                        setInterval(function () {
                            if (winScroll) {
                                winScroll = false;
                                var newWinPosition = win.scrollTop(),
                                    navPosition = navBar.scrollTop(),
                                    newNavPosition = navPosition + (newWinPosition - winPosition);
                                navBar.scrollTop(newNavPosition);
                                winPosition = newWinPosition;
                            }
                        }, 25);
                    },
                    init = function () {
                        navBar = jquery('nav.wy-nav-side:first');
                        win = jquery(window);
                    },
                    reset = function () {
                        // Get anchor from URL and open up nested nav
                        var anchor = encodeURI(window.location.hash);
                        if (anchor) {
                            try {
                                var link = $('.wy-menu-vertical')
                                    .find('[href="' + anchor + '"]');
                                $('.wy-menu-vertical li.toctree-l1 li.current')
                                    .removeClass('current');
                                link.closest('li.toctree-l2').addClass('current');
                                link.closest('li.toctree-l3').addClass('current');
                                link.closest('li.toctree-l4').addClass('current');
                            }
                            catch (err) {
                                console.log("Error expanding nav for anchor", err);
                            }
                        }
                    },
                    hashChange = function () {
                        linkScroll = true;
                        win.one('hashchange', function () {
                            linkScroll = false;
                        });
                    };
                jquery(init);
                return {
                    enable: enable,
                    hashChange: hashChange
                };
            }());
            return {
                StickyNav: stickyNav
            };
        }($));
    }

    // Add Grok the Docs Client
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/bundle-client.js",
        crossDomain: true,
        dataType: "script",
    });


    /// Out of date message

      var versionURL = [API_HOST + "/api/v1/version/", READTHEDOCS_DATA['project'],
                        "/highest/", READTHEDOCS_DATA['version'], "/?callback=?"].join("");

      $.getJSON(versionURL, onData);

      function onData (data) {
        if (data.is_highest) {
          return;
        }

        var currentURL = window.location.pathname.replace(READTHEDOCS_DATA['version'], data.slug),
            warning = $('<div class="admonition warning"> <p class="first \
                         admonition-title">Note</p> <p class="last"> \
                         You are not using the most up to date version \
                         of the library. <a href="#"></a> is the newest version.</p>\
                         </div>');

        warning
          .find('a')
          .attr('href', currentURL)
          .text(data.version);

        body = $("div.body");
        if (!body.length) {
          body = $("div.document");
        }
        body.prepend(warning);
      }


    // Override MkDocs styles
    if ("builder" in READTHEDOCS_DATA && READTHEDOCS_DATA["builder"] == "mkdocs") {
      $('<input>').attr({
          type: 'hidden',
          name: 'project',
          value: READTHEDOCS_DATA["project"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'version',
          value: READTHEDOCS_DATA["version"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'type',
          value: 'file'
      }).appendTo('#rtd-search-form');

      $("#rtd-search-form").prop("action", API_HOST + "/elasticsearch/");

      // Apply stickynav to mkdocs builds
      var nav_bar = $('nav.wy-nav-side:first'),
          win = $(window),
          sticky_nav_class = 'stickynav',
          apply_stickynav = function () {
              if (nav_bar.height() <= win.height()) {
                  nav_bar.addClass(sticky_nav_class);
              } else {
                  nav_bar.removeClass(sticky_nav_class);
              }
          };
      win.on('resize', apply_stickynav);
      apply_stickynav();
    }


    /// Search
    /// Here be dragons, this is beta quality code. Beware.

    if (build.is_rtd_theme()) {
      searchLanding();
    }

    $(document).on({
      mouseenter: function(ev) {
          var tooltip = $(ev.target).next();
          tooltip.show();
      },
      mouseleave: function(ev) {
          var tooltip = $(ev.target).next();
          tooltip.hide();
      }
    }, '.result-count');

    $(document).on('submit', '#rtd-search-form', function (ev) {
      //ev.preventDefault();
      clearSearch();
      var query = $("#rtd-search-form input[name='q']").val();
      getSearch(query, true);
    });

    $(document).on('click', '.search-result', function (ev) {
      ev.preventDefault();
      //console.log(ev.target)
      html = $(ev.target).next().html();
      displayContent(html);
    });

    function searchLanding() {
      // Highlight based on highlight GET arg
      var params = $.getQueryParameters();
      var query = (params.q) ? params.q[0].split(/\s+/) : [];
      var clear = true;
      /* Don't "search" on highlight phrases
      if (!query.length) {
        // Only clear on q
        clear = false
        var query = (params.highlight) ? params.highlight[0].split(/\s+/) : [];
      }
      */
      if (query.length) {
        query = query.join(" ");
        console.log("Searching based on GET arg for: " + query);
        $("#rtd-search-form input[name='q']").val(query);
        getSearch(query, clear);
      }
    }

    function getSearch(query, clear) {
      var get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        format: "jsonp",
        q: query
      };

      // Search results
      $.ajax({
        url: API_HOST + "/api/v2/search/section/",
        crossDomain: true,
        xhrFields: {
          withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
          clearSearch(clear);
          hits = data.results.hits.hits;
          if (!hits.length) {
            resetState();
          } else {
            displaySearch(hits, query);
          }
        },
        error: function () {
            console.log('Error searching');
        }
      });
    }

    function displayContent(html) {
        var content = $('.rst-content');
        content.html(html);
    }

    function displaySearch(hits, query) {
      FIRSTRUN = {};
      current = $(".toctree-l1.current > a");
      for (var index in hits) {
        var hit = hits[index];
        var path = hit.fields.path;
        var pageId = hit.fields.page_id;
        var title = hit.fields.title;
        var content = hit.fields.content;
        var highlight = hit.highlight.content;
        var score = hit._score;

        var li = $(".toctree-l1 > a[href^='" + path + "']");

        /*
        // This doesn't work :)
        if (!li.length && $(current.next().children()[0]).text() == title) {
            li = current
            console.log("Current page: " + title)
        } else {
          console.log("Not: " + title)
        }
        */

        var ul = li.next();

        console.log(path);

        // Display content for first result
        if (index === 0) {
          // Don't display content for now, so we show sphinx results
          //displayContent(content)
        }

        // Clear out subheading with result content
        if (!FIRSTRUN[path]) {
          li.show();
          li.attr("href", li.attr('href') + "?highlight=" + query);
          li.parent().addClass("current");
          li.append("<i style='position:absolute;right:30px;top:6px;' class='fa fa-search result-icon'></i>");
          ul.empty();
          FIRSTRUN[path] = true;
        }

        // Dedupe
        if (!FIRSTRUN[path+title]) {
          ul.append('<li class="toctree-l2">' + '<a class="reference internal search-result" pageId="' + pageId + '">' + title + '</a>' + '<span style="display: none;" class="data">' + content + '</span>' + '</li>');
          if (score > 1) {
            $(".toctree-l2 ");
            inserted = $('.toctree-l2 > [pageId="' + pageId + '"]');
            inserted.append("<i style='position:absolute;right:30px;top:6px;' class='fa fa-fire'></i>");
          }
          FIRSTRUN[path+title] = true;
        }
      }
      // Hide non-showing bits
      $.each($(".toctree-l1 > a"), function (index, el) {
          hide = true;
          if ($(el).attr('href') === "") {
              // Current page
              hide = false;
          }
          for (var key in FIRSTRUN) {
              if ($(el).attr('href').indexOf(key) === 0) {
                hide = false;
              }
          }
          if (hide) {
            $(el).hide();
          }

      });

    }

    function resetState() {
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el);
        el.show();
        el.parent().show();
      });

    }
    function clearSearch(empty) {
      $('.result-icon').remove();
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el);
        if (empty) {
          el.parent().removeClass('current');
          el.next().empty();
        }
      });
    }
});

},{"./doc":1,"./sponsorship":3}],3:[function(require,module,exports){
/* Read the Docs - Documentation promotions */

var $ = window.$;

module.exports = {
    Promo: Promo
};

function Promo (id, text, link, image) {
    this.id = id;
    this.text = text;
    this.link = link;
    this.image = image;
    this.promo = null;
}

Promo.prototype.create = function () {
    var self = this,
        nav_side = $('nav.wy-nav-side');

    if (nav_side.length) {
        // Add elements
        promo = $('<div />')
            .attr('class', 'wy-menu rst-pro');

        // Promo info
        var promo_about = $('<div />')
            .attr('class', 'rst-pro-about');
        var promo_about_link = $('<a />')
            .attr('href', 'http://docs.readthedocs.org/en/latest/sponsors.html#sponsorship-information')
            .appendTo(promo_about);
        var promo_about_icon = $('<i />')
            .attr('class', 'fa fa-info-circle')
            .appendTo(promo_about_link);
        promo_about.appendTo(promo);

        // Promo image
        if (self.image) {
            var promo_image_link = $('<a />')
                .attr('class', 'rst-pro-image-wrapper')
                .attr('href', self.link);
            var promo_image = $('<img />')
                .attr('class', 'rst-pro-image')
                .attr('src', self.image)
                .appendTo(promo_image_link);
            promo.append(promo_image_link);
        }

        // Create link with callback
        var promo_text = $('<span />')
            .html(self.text);
        $(promo_text).find('a').each(function () {
            $(this)
                .attr('class', 'rst-pro-link')
                .attr('href', self.link)
                .attr('target', '_blank')
                .on('click', function (ev) {
                    if (_gaq) {
                        _gaq.push(
                            ['rtfd._setAccount', 'UA-17997319-1'],
                            ['rtfd._trackEvent', 'Promo', 'Click', self.id]
                        );
                    }
                });
        });
        promo.append(promo_text);

        promo.appendTo(nav_side);

        promo.wrapper = $('<div />')
            .attr('class', 'rst-pro-wrapper')
            .appendTo(nav_side);

        return promo;
    }
}

// Position promo
Promo.prototype.display = function () {
    var promo = this.promo,
        self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }
    promo.show();
}

Promo.prototype.disable = function () {
}

// Variant factory method
Promo.from_variants = function (variants) {
    if (variants.length == 0) {
        return null;
    }
    var chosen = Math.floor(Math.random() * variants.length),
        variant = variants[chosen],
        text = variant.text,
        link = variant.link,
        image = variant.image,
        id = variant.id;
    return new Promo(id, text, link, image);
};

},{}]},{},[2])