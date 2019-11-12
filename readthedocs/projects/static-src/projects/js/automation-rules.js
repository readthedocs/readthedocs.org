// TODO: use knockoutjs instead, and for new code as well.

var $ = require('jquery');

function set_help_text(value) {
  var help_texts = {
    'all-versions': 'All versions will be matched.',
    'semver-versions': 'Versions incremented based on semantic versioning rules will be matched.',
    '': ''
  };
  $('#id_predefined_match_arg').siblings('.helptext').text(help_texts[value]);
}

$(function () {
  var value = $('#id_predefined_match_arg').val();
  if (value !== '') {
    $('#id_match_arg').parent().hide();
  }
  set_help_text(value);

  $('#id_predefined_match_arg').bind('change', function (ev) {
    if (this.value === '') {
      $('#id_match_arg').parent().show();
    } else {
      $('#id_match_arg').parent().hide();
    }
    set_help_text(this.value);
  });
});
