$(document).ready(function () {

    get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        page: READTHEDOCS_DATA['page'],
        theme: READTHEDOCS_DATA['theme'],
        format: "jsonp",
    }

    if ("docroot" in READTHEDOCS_DATA) {
      get_data['docroot'] = READTHEDOCS_DATA['docroot']
    }

    if (window.location.pathname.indexOf('/projects/') == 0) {
      get_data['subproject'] = true
    }

    // Theme popout code
    $.ajax({
      //url: "https://readthedocs.org/api/v2/footer_html/",
      url: "http://localhost:8000/api/v2/footer_html/",
      crossDomain: true,
      xhrFields: {
        withCredentials: true,
      },
      dataType: "jsonp",
      data: get_data,
      success: function (data) {
            if (READTHEDOCS_DATA['theme'] != "sphinx_rtd_theme") {
              $("body").append(data['html'])
            } else {
              $("div.rst-other-versions").html(data['html'])
            }
      },
      error: function () {
          console.log('Error loading footer')
      }
    });

    // Shift nav in mobile when clicking the menu.
    $(document).on('click', "[data-toggle='wy-nav-top']", function() {
      $("[data-toggle='wy-nav-shift']").toggleClass("shift");
      $("[data-toggle='rst-versions']").toggleClass("shift");
    });
    // Close menu when you click a link.
    $(document).on('click', ".wy-menu-vertical .current ul li a", function() {
      $("[data-toggle='wy-nav-shift']").removeClass("shift");
      $("[data-toggle='rst-versions']").toggleClass("shift");
    });
    $(document).on('click', "[data-toggle='rst-current-version']", function() {
      $("[data-toggle='rst-versions']").toggleClass("shift-up");
    });  
    // Make tables responsive
    $("table.docutils:not(.field-list)").wrap("<div class='wy-table-responsive'></div>");
    
    // Add Grok the Docs Client
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/bundle-client.js",
        crossDomain: true,
        dataType: "script",
    });

    if (READTHEDOCS_DATA['theme'] == 'sphinx_rtd_theme') {
      searchLanding()
    }

    // Search

    /*  Hide tooltip display for now */
    $(document).on({
      mouseenter: function(ev) {
          var tooltip = $(ev.target).next()
          tooltip.show()
      },
      mouseleave: function(ev) {
          var tooltip = $(ev.target).next()
          tooltip.hide()
      }
    }, '.result-count')
    $(document).on('submit', '#rtd-search-form', function (ev) {
      ev.preventDefault();
      clearSearch()
      var query = $("#rtd-search-form input[name='q'").val()
      getSearch(query)
    }) 
    $(document).on('click', '.search-result', function (ev) {
      ev.preventDefault();
      console.log(ev.target)
      html = $(ev.target).next().html()
      displayContent(html);
    }) 
    /**/

    function searchLanding() {
      // Highlight based on highlight GET arg
      var params = $.getQueryParameters();
      var query = (params.highlight) ? params.highlight[0].split(/\s+/) : [];
      if (!query.length) {
        var query = (params.q) ? params.q[0].split(/\s+/) : [];
      }
      if (query.length) {
        query = query.join(" ")
        console.log("Searching based on GET arg for: " + query)
        getSearch(query)
      }
    }

    function getSearch(query) {
      var get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        format: "jsonp",
        q: query
      }

      // Search results
      $.ajax({
        //url: "https://readthedocs.org/api/v2/search/",
        url: "http://localhost:8000/api/v2/search/section/",
        crossDomain: true,
        xhrFields: {
          withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
          clearSearch()
          hits = data.results.hits.hits
          if (!hits.length) {
            resetState()
          } else {
            displaySearch(hits)
          }
        },
        error: function () {
            console.log('Error searching')
        }
      });
    }

    function displayContent(html) {
        var content = $('.rst-content')
        content.html(html)
    }

    function displaySearch(hits) {
      FIRSTRUN = {}
      for (index in hits) {
        var hit = hits[index]
        var path = hit.fields.path
        var pageId = hit.fields.page_id
        var title = hit.fields.title
        var content = hit.fields.content
        var highlight = hit.highlight.content

        var li = $(".toctree-l1 > a[href^='" + path + "']")
        var ul = li.next()

        console.log(path)

        // Display content for first result
        if (index == 0) {
          displayContent(content)
        }

        // Clear out subheading with result content
        if (!FIRSTRUN[path]) {
          li.show()
          li.parent().addClass("current")
          li.append("<i style='position:absolute;right:30px;top:6px;' class='icon icon-search result-icon'></i>")
          ul.empty()
          FIRSTRUN[path] = true
        }

        // Dedupe
        if (!FIRSTRUN[path+title]) {
          ul.append('<li class="toctree-l2">' + '<a class="reference internal search-result" href="' + pageId + '">' + title + '</a>' + '<span style="display: none;" class="data">' + content + '</span>' + '</li>')
          //inserted = $('.toctree-l2 > a[href="' + pageId + '"]')
          //inserted.append("<span class='result-count' style='position:absolute;right:30px;top:6px;'>" + index + "</span>")
          FIRSTRUN[path+title] = true
        }



        //li.append("<div style='display: none;' class='tooltip'>" + highlight + "</div>")
      }
      $.each($(".toctree-l1 > a"), function (index, el) {
          hide = true
          for (key in FIRSTRUN) {
              if ($(el).attr('href').indexOf(key) == 0) {
                hide = false
              }
          }
          if (hide) {
            console.log("Hiding " + el)
            $(el).hide()
          }

      })

    }

    function resetState() {
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el)
        el.show()
        el.parent().show()
        el.next().empty()
      })

    }
    function clearSearch() {
      $('.result-icon').remove()
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el)
        el.parent().removeClass('current')
        el.next().empty()
      })
    }

})
