(function () {
  $(function() {
    var input = $('#id_repo'),
        repo = $('#id_repo_type');

    input.blur(function () {
      var val = input.val(),
          type;

      switch(true) {
        case /bitbucket/.test(val):
        case /^hg/.test(val):
          type = 'hg';
        break;

        case /^bzr/.test(val):
        case /launchpad/.test(val):
          type = 'bzr';
        break;

        case /trunk/.test(val):
        case /^svn/.test(val):
          type = 'svn';
        break;

        default:
        case /github/.test(val):
        case /(^git|\.git$)/.test(val):
          type = 'git';
        break;
      }

      repo.val(type);
    });
  });

})();
