/* Site-specific javascript */

// Dismiss a notification
module.exports.handle_notification_dismiss = function () {
  $(document).ready(function () {
    $('ul.notifications li.notification > a.notification-action').click(function (ev) {
      var url = $(this).attr('href');
      var dismiss_url = $(this).parent().attr('data-dismiss-url');
      var csrf_token = $(this).parent().attr('data-csrf-token');
      if (dismiss_url) {
        ev.preventDefault();
        $.ajax({
          type: "PATCH",
          url: dismiss_url,
          data: {
            state: "dismissed",
          },
          headers: {
            "X-CSRFToken": csrf_token,
          },
        }).then((data) => {
          $(this).parent().hide();
        });
      }
      else {
        $(this).parent().hide();
      }
    });
  });
};
