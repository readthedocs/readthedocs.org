$(document).ready(function()
{
    ShowActionOnOver();
    guessRepo();
    checkVersion();
    getVersions();
    Search.init();
});

warning = '<div class="admonition note"> <p class="first admonition-title">Note</p> <p class="last"> You are not using the most up to date version of the library. '

 function checkVersion() {
    // doc_slug and doc_version MUST be defined or else the error prevents
    // Firefox from using any jQuery
    if (typeof doc_slug === 'undefined') 
        doc_slug = ""
    if (typeof doc_version === 'undefined') 
        doc_version = ""
    $.ajax({
     type: 'GET',
     url: "http://readthedocs.org/api/v1/version/" + doc_slug + "/highest/" + doc_version + "/",
     //url: "/api/v1/version/" + doc_slug + "/highest/" + doc_version + "/",
     success: function(data, textStatus, request) {
      if (!data.is_highest) {
        current_url = window.location.pathname.replace(doc_version, data.slug)
         $("div.body").prepend(warning + "<a href='" + current_url  + "'>" + data.version + "</a> is the newest version. </p></div>")
      }
     },
     dataType: 'jsonp'
    });
 }

 function getVersions() {
    $.ajax({
     type: 'GET',
     //This has to be hard coded for CNAMEs, subdomains.
     url: "http://readthedocs.org/api/v1/version/" + doc_slug + "/?active=True",
     //url: "/api/v1/version/" + doc_slug + "/?active=True",
     success: function(data, textStatus, request) {
        $('#version_menu,.version-listing').empty()
        $('#sidebar_versions').empty()
        for (key in data['objects']) {
            obj = data['objects'][key]
            current_url = window.location.pathname.replace(doc_version, obj.slug)
            // Update widget
            $("#version_menu,.version-listing").append('<li><a href="' + current_url + '">' + obj.slug + '</a></li>')
            // Update sidebar
            $("#sidebar_versions").append('<li><a href="' + current_url + '">' + obj.slug + '</a></li>')
          }
     },
     dataType: 'jsonp'
    });
 }

 function ShowActionOnOver()
 {
   $(".module-item-menu").hover(
       function()
       {
          $(".hidden-child",this).show();
       },
       function()
       {
           $(".hidden-child",this).hide();
        }
    );
 }

function guessRepo() {
  $("#id_repo").blur(
      function() {
         val = this.value
         repo = $("#id_repo_type")[0]
         if (val.indexOf("git") >= 0) {
            repo.value = "git"
         }
         else if (val.indexOf("bitbucket") >= 0) {
            repo.value = "hg"
         }
         else if (val.indexOf("hg") >= 0) {
            repo.value = "hg"
         }
         else if (val.indexOf("bzr") >= 0) {
            repo.value = "bzr"
         }
         else if (val.indexOf("launchpad") >= 0) {
            repo.value = "bzr"
         }
         else if (val.indexOf("trunk") >= 0) {
            repo.value = "svn"
         }
         else if (val.indexOf("svn") >= 0) {
            repo.value = "svn"
         }
      }
  )
}


(function () {

    // Constructor.
    this.BuildUpdater = function(buildId) {
        this.buildId = buildId;
        this.buildUrl = '/api/v1/build/' + this.buildId;
        this.buildDiv = 'div#build-' + this.buildId;
        this.buildLoadingImg = this.buildDiv + ' img.build-loading';
        this.intervalId = null;
    };

    BuildUpdater.prototype.stopPolling = function() {
        $(this.buildLoadingImg).addClass('hide');
        clearInterval(this.intervalId);
    };

    // Show an animated 'loading' gif while we get the current details of the build
    // with `buildId` from the server.
    //
    // On success, hide the loading gif, populate any <span> nodes that have ids
    // matching the pattern "build-<field name in `data` object>" and clear
    // `this.intervalId`.
    BuildUpdater.prototype.updateBuildDetails = function(data) {
        var _this = this;

        for (var prop in data) {
            if (data.hasOwnProperty(prop)) {
                var val = data[prop];
                var el = $(this.buildDiv + ' span#build-' + prop);

                if (prop == 'success') {
                    val = val ? "Passed" : "Failed";
                }

                if (prop == 'state') {
                    val = val.charAt(0).toUpperCase() + val.slice(1);
                    
                    if (val == 'Finished') {
                        _this.stopPolling();
                    }
                }

                if (el) {
                    el.text(val);
                }
            }
        }
    };

    BuildUpdater.prototype.getBuildDetails = function() {
        var _this = this;

        $.get(this.buildUrl, function(data) {
            _this.updateBuildDetails(data);
        });
    };

    // If the build with ID `this.buildId` has a state other than finished, poll
    // the server every 5 seconds for the current status. Update the details
    // page with the latest values from the server, to keep the user informed of
    // progress.
    //
    // If we haven't received a 'finished' state back the server in 10 minutes,
    // stop polling.
    BuildUpdater.prototype.startPolling = function() {
        var stateSpan = $(this.buildDiv + ' span#build-state');
        var _this = this;

        // If the build is already finished, or it isn't displayed on the page,
        // ignore it.
        if (stateSpan.text() == 'Finished' || stateSpan.length === 0) {
            return;
        }

        $(this.buildLoadingImg).removeClass('hide');

        this.getBuildDetails();

        var intervalId = setInterval(function () {
            _this.getBuildDetails();
        }, 5000);

        // Stop polling after 10 minutes, in case the build never finishes.
        setTimeout(function() {
            _this.stopPolling();
        }, 600000);
    };

}).call(this);

