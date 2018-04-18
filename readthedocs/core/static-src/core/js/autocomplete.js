var $ = require('jquery');
var jqueryui = require('jquery-ui');

module.exports = function (selector, url) {
  $(selector).autocomplete({
    source: url,
    minLength: 2,
    open: function (event, ui) {
      var ac_top = $('.ui-autocomplete').css('top');
      $('.ui-autocomplete').css({'width': '233px', 'top': ac_top + 10 });
    }
  });
};
