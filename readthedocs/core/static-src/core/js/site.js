/* Site-specific javascript */

// Notifications that can both dismiss and point to a separate URL
module.exports.handle_notification_dismiss = function () {
  $(document).ready(function () {
    $('ul.notifications li.notification > a').click(function (ev) {
      var url = $(this).attr('href');
      var dismiss_url = $(this).parent().attr('data-dismiss-url');
      if (dismiss_url) {
        ev.preventDefault();
        $.get(dismiss_url, function (data, text_status, xhr) {
          window.location.href = url;
        });
      }
      else {
        $(this).hide();
      }
    });
  });
}
