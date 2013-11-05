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
      url: "https://readthedocs.org/api/v2/footer_html/",
      //url: "http://localhost:8000/api/v2/footer_html/",
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


    // Search

    $(document).on({
      mouseenter: function(ev) {
          tooltip = $(ev.target).next()
          tooltip.show()
      },
      mouseleave: function(ev) {
          tooltip = $(ev.target).next()
          tooltip.hide()
      }
    }, '.result-count')

    $(document).on('submit', '#rtd-search-form', function (ev) {
      ev.preventDefault();
      query = $("#rtd-search-form input[name='q'").val()
      get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        format: "jsonp",
        q: query
      }

      // Theme popout code
      $.ajax({
        //url: "https://readthedocs.org/api/v2/search/",
        url: "http://localhost:8000/api/v2/search/",
        crossDomain: true,
        xhrFields: {
          withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
          $('.result-count').remove()
          hits = data.results.hits.hits
          for (index in hits) {
            hit = hits[index]
            page = hit.fields.page
            title = hit.fields.title
            highlight = hit.highlight.content
            li = $(".wy-menu a:contains('" + title + "')")
            console.log(li)
            li.append("<span class='result-count' style='position:absolute;right:30px;top:6px;'>" + 1 + "</span>")
            li.append("<div style='display: none;' class='tooltip'>" + highlight + "</div>")
          }
        },
        error: function () {
            console.log('Error searching')
        }
      });
    }) // End on submit of search

    
    // Add Grok the Docs Client
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/bundle-client.js",
        crossDomain: true,
        dataType: "script",
    });


})
