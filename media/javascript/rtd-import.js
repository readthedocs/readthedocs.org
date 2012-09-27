(function () {
  "use strict";

  $(document).ready(function () {
    $("#id_repo").blur(function () {
      var val = this.value,
          repo = $("#id_repo_type")[0];

      if (val.indexOf("git") >= 0) {
        repo.value = "git";
      } else if (val.indexOf("bitbucket") >= 0) {
        repo.value = "hg";
      } else if (val.indexOf("hg") >= 0) {
        repo.value = "hg";
      } else if (val.indexOf("bzr") >= 0) {
        repo.value = "bzr";
      } else if (val.indexOf("launchpad") >= 0) {
        repo.value = "bzr";
      } else if (val.indexOf("trunk") >= 0) {
        repo.value = "svn";
      } else if (val.indexOf("svn") >= 0) {
        repo.value = "svn";
      }
    });
  });

})();
