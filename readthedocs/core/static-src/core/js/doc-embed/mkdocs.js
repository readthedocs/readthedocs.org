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

      var search_url = window.location.protocol + "//" + window.location.hostname +
                       "/" + rtd.language + "/" + rtd.version + "/search.html";
      $("#rtd-search-form").prop("action", search_url);

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
