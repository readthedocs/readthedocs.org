 $(document).ready(function()
 {
    ShowActionOnOver();
    guessRepo();
    checkVersion();
    getVersions();
 });

warning = '<div class="admonition note"> <p class="first admonition-title">Note</p> <p class="last"> You are not using the most up to date version of the library. '

 function checkVersion() {
    $.ajax({
     type: 'GET',
     url: "http://readthedocs.org/api/v1/version/" + doc_slug + "/highest/" + doc_version + "/",
     //url: "/api/v1/version/" + doc_slug + "/highest/" + doc_version + "/",
     success: function(data, textStatus, request) {
      if (!data.is_highest) {
         $("div.body").prepend(warning + "<a href='http://readthedocs.org" + window.location.pathname.replace(doc_version, data.slug)  + "'>" + data.version + "</a> is the newest version. </p></div>")
      }
     },
     dataType: 'jsonp'
    });
 }

 function getVersions() {
    $('#version_menu').empty()
    $.ajax({
     type: 'GET',
     //This has to be hard coded for CNAMEs, subdomains.
     url: "http://readthedocs.org/api/v1/version/" + doc_slug + "/?active=True",
     //url: "/api/v1/version/" + doc_slug + "/?active=True",
     success: function(data, textStatus, request) {
        for (key in data['objects']) {
            obj = data['objects'][key]
            current_url = window.location.pathname.replace(doc_version, obj.slug)
            $("#version_menu").append('<li><a href="' + current_url + '">' + obj.slug + '</a></li>')
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

