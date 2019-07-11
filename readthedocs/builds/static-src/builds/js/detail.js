// Build detail view

var ko = require('knockout');
var $ = require('jquery');


function BuildCommand(data) {
    var self = this;
    self.id = ko.observable(data.id);
    self.command = ko.observable(data.command);
    self.output = ko.observable(data.output);
    self.exit_code = ko.observable(data.exit_code || 0);
    self.successful = ko.observable(self.exit_code() === 0);
    self.run_time = ko.observable(data.run_time);
    self.is_showing = ko.observable(!self.successful());

    self.toggleCommand = function () {
        self.is_showing(!self.is_showing());
    };

    self.command_status = ko.computed(function () {
        return self.successful() ?
            'build-command-successful' :
            'build-command-failed';
    });
}

function BuildDetailView(instance) {
    var self = this;
    var instance = instance || {};

    /* Instance variables */
    self.state = ko.observable(instance.state);
    self.state_display = ko.observable(instance.state_display);
    self.finished = ko.computed(function () {
        return self.state() === 'finished';
    });
    self.date = ko.observable(instance.date);
    self.success = ko.observable(instance.success);
    self.error = ko.observable(instance.error);
    self.length = ko.observable(instance.length);
    self.commands = ko.observableArray(instance.commands);
    self.display_commands = ko.computed(function () {
        var commands_display = [];
        var commands_raw = self.commands();
        var n;
        for (n in commands_raw) {
            var command = new BuildCommand(commands_raw[n]);
            commands_display.push(command);
        }
        return commands_display;
    });
    self.commit = ko.observable(instance.commit);
    self.docs_url = ko.observable(instance.docs_url);
    self.vcs_url = ko.observable(instance.vcs_url);

    /* Others */
    self.legacy_output = ko.observable(false);
    self.show_legacy_output = function () {
        self.legacy_output(true);
    };

    function poll_api() {
        if (self.finished()) {
            return;
        }
        $.getJSON('/api/v2/build/' + instance.id + '/', function (data) {
            self.state(data.state);
            self.state_display(data.state_display);
            self.date(data.date);
            self.success(data.success);
            self.error(data.error);
            self.length(data.length);
            self.commit(data.commit);
            self.docs_url(data.docs_url);
            self.vcs_url(data.vcs_url);
            var n;
            for (n in data.commands) {
                var command = data.commands[n];
                var match = ko.utils.arrayFirst(
                    self.commands(),
                    function (command_cmp) {
                        return (command_cmp.id === command.id);
                    }
                );
                if (!match) {
                    self.commands.push(command);
                }
            }
        });

        setTimeout(poll_api, 2000);
    }

    poll_api();
}

BuildDetailView.init = function (instance, domobj) {
    var view = new BuildDetailView(instance);
    var domobj = domobj || $('#build-detail')[0];
    ko.applyBindings(view, domobj);
    return view;
};

module.exports.BuildDetailView = BuildDetailView;
