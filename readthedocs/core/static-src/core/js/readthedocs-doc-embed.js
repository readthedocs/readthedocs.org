var sponsorship = require('./sponsorship'),
    doc = require('./doc'),
    grokthedocs = require('./doc-embed/grokthedocs-client');

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

    grokthedocs.init();

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
    
});
