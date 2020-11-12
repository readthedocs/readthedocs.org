// TODO: use knockoutjs instead, and for new code as well.

var $ = require('jquery');


function set_match_help_text(value) {
  var help_texts = {
    'all-versions': 'All versions will be matched.',
    'semver-versions': 'Versions incremented based on semantic versioning rules will be matched.',
    '': ''
  };
  $('#id_predefined_match_arg').siblings('.helptext').text(help_texts[value]);
}

function set_action_help_text() {
  var action_arg = $('#id_action_arg');
  if (action_arg.val() === '') {
    action_arg.val('^main$');
  }
  action_arg.siblings('label').text('Base branch:');
  action_arg.siblings('.helptext').html(
    'Pattern to match the base branch. '
    + '<a href="https://docs.readthedocs.io/page/automation-rules.html#user-defined-matches">'
    + 'Check the documentation'
    + '</a> '
    + 'for valid patterns.'
  );
}


function reset_actions(type) {
  var actions = {
    '': '---------',
    'activate-version': 'Activate version',
    'delete-version': 'Hide version',
    'hide-version': 'Make version public',
    'make-version-public': 'Make version private',
    'make-version-private': 'Set version as default',
    'set-default-version': 'Delete version (on branch/tag deletion)',
  };
  if (type === 'external') {
    actions = {
      '': '---------',
      'build-external-version': 'Build version',
    };
  }
  var element = $('#id_action');
  var current = $('#id_action :selected').val();
  element.empty();
  $.each(actions, function (key, value) {
    var option = $("<option></option>").attr("value", key).text(value);
    if (key === current) {
      option.attr('selected', true);
    }
    element.append(option);
  });
}


$(function () {
  // Match
  var value = $('#id_predefined_match_arg').val();
  if (value !== '') {
    $('#id_match_arg').parent().hide();
  }
  set_match_help_text(value);

  $('#id_predefined_match_arg').bind('change', function (ev) {
    if (this.value === '') {
      $('#id_match_arg').parent().show();
    } else {
      $('#id_match_arg').parent().hide();
    }
    set_match_help_text(this.value);
  });

  // Action argument
  var type = $('#id_version_type').val();
  if (type !== 'external') {
    $('#id_action_arg').parent().hide();
  }
  set_action_help_text();
  reset_actions(type);

  $('#id_version_type').bind('change', function (e) {
    if (this.value === 'external') {
      set_action_help_text();
      $('#id_action_arg').parent().show();
    } else {
      $('#id_action_arg').parent().hide();
    }
    reset_actions(this.value);
  });
});
