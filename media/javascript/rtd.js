$(document).ready(function()
{
    ShowActionOnOver();
    guessRepo();
    checkVersion();
    getVersions();
    instantSearch();
});

warning = '<div class="admonition note"> <p class="first admonition-title">Note</p> <p class="last"> You are not using the most up to date version of the library. '

 function checkVersion() {
    // doc_slug and doc_version MUST be defined or else the error prevents
    // Firefox from using any jQuery
    doc_slug = ""
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

