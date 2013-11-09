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

    if (window.location.pathname.match((/^\/projects/))) {
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
          displaySearch(hits)
        },
        error: function () {
            console.log('Error searching')
        }
      });
    }

    function displaySearch(hits) {
      var ul = $('.wy-menu-vertical > ul')
      ul.empty()
      for (index in hits) {
        var hit = hits[index]
        var page = hit.fields.page
        var title = hit.fields.title
        var highlight = hit.highlight.content
        var li  = $(".wy-menu a").filter(function() {
            return $(this).text() === title;
        })
        var content = $('.rst-content')

        ul.append('<li class="toctree-l1">' + title + '</li>')
        if (index == 0) {
          content.html(hit.fields.content)
        }

        //li.append("<i style='position:absolute;right:30px;top:6px;' class='icon icon-search result-icon'></i>")
        //li.append("<span class='result-count' style='position:absolute;right:30px;top:6px;'>" + 1 + "</span>")
        //li.append("<div style='display: none;' class='tooltip'>" + highlight + "</div>")
      }
    }

    function clearSearch() {
      $('.result-icon').remove()
    }

})
