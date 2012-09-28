(function () {
  var checkVersion = function (slug, version) {
    var versionURL = ["//readthedocs.org/api/v1/version/", slug,
                      "/highest/", version, "/"].join("");

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
                       "/?active=True"].join("");

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
      }

      // update widget and sidebar
      $('#version_menu, .version-listing, #sidebar_versions').html(items.html())
    }
  };

  $(function () {
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

    Search.init();
  });

})();
