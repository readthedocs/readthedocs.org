var $ = require('jquery'),
    jqueryui = require('jquery-ui');

module.exports = function (selector, url) {
  $(selector).autocomplete({
    source: url,
    minLength: 2,
    open: function(event, ui) {
      ac_top = $('.ui-autocomplete').css('top');
      $('.ui-autocomplete').css({'width': '233px', 'top': ac_top + 10 });
    }
  });
}
