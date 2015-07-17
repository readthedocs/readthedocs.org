(function () {
  $(function() {
    var input = $('#id_repo'),
        repo = $('#id_repo_type');

    input.blur(function () {
      var val = input.val(),
          type;

      switch(true) {
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

    $('[data-sync-repositories]').each(function () {
      var $button = $(this);
      var target = $(this).attr('data-target');

      $button.on('click', function () {
        var url = $button.attr('data-sync-repositories');
        $.ajax({
          method: 'POST',
          url: url,
          success: function (data) {
            $button.attr('disabled', true);
            watchProgress(data.url);
          },
          error: function () {
            onError();
          }
        });
        $('.sync-repositories').addClass('hide');
        $('.sync-repositories-progress').removeClass('hide');
      });

      function watchProgress(url) {
        setTimeout(function () {
          $.ajax({
            method: 'GET',
            url: url,
            success: function (data) {
              if (data.finished) {
                if (data.success) {
                  onSuccess();
                } else {
                  onError();
                }
              } else {
                watchProgress(url);
              }
            },
            error: function () {
              watchProgress(url);
            }
          });
        }, 2000);
      }

      function onSuccess(url) {
        $.ajax({
          method: 'GET',
          url: window.location.href,
          success: function (data) {
            var $newContent = $(data).find(target);
            $('body').find(target).replaceWith($newContent);
            $('.sync-repositories').addClass('hide');
            $('.sync-repositories-progress').addClass('hide');
            $('.sync-repositories-success').removeClass('hide');
          },
          error: onError
        });
      }

      function onError() {
        $('.sync-repositories').addClass('hide');
        $('.sync-repositories-progress').addClass('hide');
        $('.sync-repositories-error').removeClass('hide');
      }
    });
  });

})();
