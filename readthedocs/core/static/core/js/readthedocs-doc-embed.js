(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
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
            && this.is_rtd_theme()
           );
};

},{}],2:[function(require,module,exports){
var Build = require('./build').Build;
var rtddata = require('./rtd-data');
var versionCompare = require('./version-compare');


function init() {
    var rtd = rtddata.get();

    var get_data = {
        project: rtd['project'],
        version: rtd['version'],
        page: rtd['page'],
        theme: rtd['theme'],
        format: "jsonp",
    };

    // Crappy heuristic, but people change the theme name on us.
    // So we have to do some duck typing.
    if ("docroot" in rtd) {
        get_data['docroot'] = rtd['docroot'];
    }

    if ("source_suffix" in rtd) {
        get_data['source_suffix'] = rtd['source_suffix'];
    }

    if (window.location.pathname.indexOf('/projects/') === 0) {
        get_data['subproject'] = true;
    }

    // Get footer HTML from API and inject it into the page.
    $.ajax({
        url: rtd.api_host + "/api/v2/footer_html/",
        crossDomain: true,
        xhrFields: {
            withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
            versionCompare.init(data.version_compare);
            injectFooter(data);
            setupBookmarkCSRFToken();
        },
        error: function () {
            console.error('Error loading Read the Docs footer');
        }
    });
}


function injectFooter(data) {
    var build = new Build(rtddata.get());

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
        var promo = new sponsorship.Promo(
            data.promo_data.id,
            data.promo_data.text,
            data.promo_data.link,
            data.promo_data.image
        )
        if (promo) {
            promo.display();
        }
    }
}


function setupBookmarkCSRFToken() {
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
}


module.exports = {
    init: init
};

},{"./build":1,"./rtd-data":5,"./version-compare":7}],3:[function(require,module,exports){
function init() {
    // Add Grok the Docs Client
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/bundle-client.js",
        crossDomain: true,
        dataType: "script",
    });
}


module.exports = {
    init: init
};

},{}],4:[function(require,module,exports){
/*
 * Mkdocs specific JS code.
 */


var rtddata = require('./rtd-data');


function init() {
    var rtd = rtddata.get();

    // Override MkDocs styles
    if ("builder" in rtd && rtd["builder"] == "mkdocs") {
      $('<input>').attr({
          type: 'hidden',
          name: 'project',
          value: rtd["project"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'version',
          value: rtd["version"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'type',
          value: 'file'
      }).appendTo('#rtd-search-form');

      $("#rtd-search-form").prop("action", rtd.api_host + "/elasticsearch/");

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

}


module.exports = {
    init: init
};

},{"./rtd-data":5}],5:[function(require,module,exports){
/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */


/*
 * Access READTHEDOCS_DATA on call, not on module load. The reason is that the
 * READTHEDOCS_DATA might not be available during script load time.
 */
function get() {
    return $.extend({
        api_host: 'https://readthedocs.org'
    }, window.READTHEDOCS_DATA);
}


module.exports = {
    get: get
};

},{}],6:[function(require,module,exports){
/*
 * Sphinx builder specific JS code.
 */


var rtddata = require('./rtd-data');


function init() {
    var rtd = rtddata.get();

    /// Click tracking on flyout
    $(document).on('click', "[data-toggle='rst-current-version']", function() {
      var flyout_state = $("[data-toggle='rst-versions']").hasClass('shift-up') ? 'was_open' : 'was_closed'
      if (_gaq) {
        _gaq.push(
            ['rtfd._setAccount', 'UA-17997319-1'],
            ['rtfd._trackEvent', 'Flyout', 'Click', flyout_state]
        );
      }
    });

    /// Read the Docs Sphinx theme code
    if (!("builder" in rtd) || "builder" in rtd && rtd["builder"] != "mkdocs") {
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

}


module.exports = {
    init: init
};

},{"./rtd-data":5}],7:[function(require,module,exports){
var rtddata = require('./rtd-data');


function init(data) {
    var rtd = rtddata.get();

    /// Out of date message

    if (data.is_highest) {
        return;
    }

    var currentURL = window.location.pathname.replace(rtd['version'], data.slug);
    var warning = $(
        '<div class="admonition warning"> ' +
        '<p class="first admonition-title">Note</p> ' +
        '<p class="last"> ' +
        'You are not using the most up to date version of the library. ' +
        '<a href="#"></a> is the newest version.' +
        '</p>' +
        '</div>');

    warning
      .find('a')
      .attr('href', currentURL)
      .text(data.version);

    var body = $("div.body");
    if (!body.length) {
        body = $("div.document");
    }
    body.prepend(warning);
}


module.exports = {
    init: init
};

},{"./rtd-data":5}],8:[function(require,module,exports){
var sponsorship = require('./sponsorship'),
    footer = require('./doc-embed/footer.js'),
    grokthedocs = require('./doc-embed/grokthedocs-client'),
    mkdocs = require('./doc-embed/mkdocs'),
    rtddata = require('./doc-embed/rtd-data'),
    sphinx = require('./doc-embed/sphinx');

$(document).ready(function () {
    footer.init();
    sphinx.init();
    grokthedocs.init();
    mkdocs.init();
});

},{"./doc-embed/footer.js":2,"./doc-embed/grokthedocs-client":3,"./doc-embed/mkdocs":4,"./doc-embed/rtd-data":5,"./doc-embed/sphinx":6,"./sponsorship":9}],9:[function(require,module,exports){
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

        // On Click handler
        function promo_click() {
            if (_gaq) {
                _gaq.push(
                    ['rtfd._setAccount', 'UA-17997319-1'],
                    ['rtfd._trackEvent', 'Promo', 'Click', self.id]
                );
            }
        }

        // Promo image
        if (self.image) {
            var promo_image_link = $('<a />')
                .attr('class', 'rst-pro-image-wrapper')
                .attr('href', self.link)
                .attr('target', '_blank')
                .on('click', promo_click);
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
                .on('click', promo_click);
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

},{}]},{},[8]);
