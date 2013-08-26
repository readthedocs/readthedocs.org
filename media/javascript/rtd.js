(function () {
  var checkVersion = function (slug, version) {
    var versionURL = ["//readthedocs.org/api/v1/version/", slug,
                      "/highest/", version, "/?callback=?"].join("");

    $.getJSON(versionURL, onData);

    function onData (data) {
      if (data.is_highest) {
        return;
      }

      var currentURL = window.location.pathname.replace(version, data.slug),
          warning = $('<div class="admonition note"> <p class="first \
                       admonition-title">Note</p> <p class="last"> \
                       You are not using the most up to date version \
                       of the library. <a href="#"></a> is the newest version.</p>\
                       </div>');

      warning
        .find('a')
        .attr('href', currentURL)
        .text(data.version);

      $("div.body").prepend(warning);
    }

  };

  var getVersions = function (slug, version) {
    var versionsURL = ["//readthedocs.org/api/v1/version/", slug,
                       "/?active=True&callback=?"].join("");

    return $.getJSON(versionsURL, gotData);

    function gotData (data) {
      var items = $('<ul />')
        , currentURL
        , versionItem
        , object

      for (var key in data.objects) {
        object = data.objects[key]
        currentURL = window.location.pathname.replace(version, object.slug)
        versionItem = $('<a href="#"></a>')
          .attr('href', currentURL)
          .text(object.slug)
          .appendTo($('<li />').appendTo(items))
      }

      // update widget and sidebar
      $('#version_menu, .version-listing, #sidebar_versions').html(items.html())
    }
  };

  $(function () {
    // Code executed on load
    var slug = window.doc_slug,
        version = window.doc_version;

    // Show action on hover
    $(".module-item-menu").hover(
      function () {
        $(".hidden-child", this).show();
      }, function () {
        $(".hidden-child", this).hide();
      }
    );

    checkVersion(slug, version);
    getVersions(slug, version);


  });

})();

/*
 * Grok the Docs event handling
 * This will allow you to better 
 * understand whats happening in your docs,
 * once fully rolled out.
*/


$.ajax({
url: "//api.grokthedocs.com/static/client.js",
crossDomain: true,
dataType: "script",
cache: true,
});

// Google Analytics Custom bits

$(document).ready( function () {
_gaq.push(['_setCustomVar',
      1,                   // This custom var is set to slot #1.  Required parameter.
      'Project',           // The top-level name for your online content categories.  Required parameter.
      doc_slug,  // Sets the value of "Section" to "Life & Style" for this particular aricle.  Required parameter.
      3                    // Sets the scope to page-level.  Optional parameter.
   ]);

_gaq.push(['_setCustomVar',
      1,                   // This custom var is set to slot #1.  Required parameter.
      'Version',           // The top-level name for your online content categories.  Required parameter.
      doc_version,  // Sets the value of "Section" to "Life & Style" for this particular aricle.  Required parameter.
      3                    // Sets the scope to page-level.  Optional parameter.
   ]);

_gaq.push(['_setCustomVar',
      1,                   // This custom var is set to slot #1.  Required parameter.
      'Page',           // The top-level name for your online content categories.  Required parameter.
      page_name,  // Sets the value of "Section" to "Life & Style" for this particular aricle.  Required parameter.
      3                    // Sets the scope to page-level.  Optional parameter.
   ]);
})
