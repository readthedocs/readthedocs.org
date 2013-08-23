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

  function logHashChange(project, version, page, id, hash) {
    $.ajax({
      type: 'POST',
      url: 'http://api.grokthedocs.com/api/v1/actions/',
      crossDomain: true,
      data: {
        project: project,
        version: version,
        page: page,
        object_slug: id,
        hash: hash,
        url: window.location.href,
        type: "hashchange"
      },
      success: function(data, textStatus, request) {
        console.log("Sent hash change data")
      },
      error: function(request, textStatus, error) {
        console.log("Error sending hash change data")
      }
    });
  }

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


    // Click tracking code
    window.onhashchange = function(ev) {
      var element = document.getElementById((window.location.hash || '').slice(1))
      var project = doc_slug
      var version = doc_version
      var page = page_name
      var id = element.id
        if (typeof element.hash != "undefined") {
            var hash = element.hash
        } else {
          var hash = null
        }
      logHashChange(project, version, page, id, hash);
    }



  });

})();
