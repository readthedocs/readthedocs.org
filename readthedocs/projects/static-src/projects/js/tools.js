var rtd = require('readthedocs-client'),
    ko = require('knockout'),
    $ = null;

if (typeof(window) == 'undefined') {
    require('jquery');
}
else {
    $ = window.$;
}

function EmbedView (config) {
    var self = this,
        project = 'rtfd';

    // Normalize config
    self.config = config || {};
    if (typeof(self.config.api_host) == 'undefined') {
        self.config.api_host = 'https://readthedocs.org'
    }

    self.help = ko.observable(null);

    self.project = ko.observable('blog');
    self.file = ko.observable(null);

    self.sections = ko.observableArray();
    ko.computed(function () {
        var file = self.file();
        self.sections.removeAll();
        if (! file) {
            return;
        }
        self.help('Loading');
        self.section(null);

        $.ajax({
            type: 'GET',
            url: self.config.api_host + '/api/v1/embed/',
            crossDomain: true,
            data: {
                project: project,
                doc: file
            }
        })
        .done(function(data, text_status, request) {
            self.sections.removeAll();
            self.help(null);
            var sections_data = [];
            for (n in data.headers) {
                var section = data.headers[n];
                $.each(section, function (title, id) {
                    sections_data.push({
                        title: title,
                        id: id
                    });
                });
            }
            self.sections(sections_data);
        })
        .fail(function(data, text_status, error) {
            self.help('There was a problem retrieving data from the API');
        });
    });

    self.has_sections = ko.computed(function () {
        return (self.sections().length > 0);
    });

    self.section = ko.observable(null);

    self.has_section = ko.computed(function () {
        return (self.section() != null && self.section() != '');
    });

    self.response = ko.observable(null);
    ko.computed(function () {
        var file = self.file(),
            section = self.section();
        if (file == null || section == null) {
            return self.response(null);
        }
        self.help('Loading');
        self.response(null);

        $.ajax({
            type: 'GET',
            url: self.config.api_host + '/api/v1/embed/',
            crossDomain: true,
            xhrFields: {
                withCredentials: true,
            },
            data: {
                project: project,
                doc: file,
                section: section
            },
        })
        .done(function (data, text_status, request) {
            self.help(null);
            self.response(data.content);
        })
        .fail(function(request, text_status, error) {
            self.help('There was a problem retrieving data from the API');
        })
    });

    self.has_response = ko.computed(function () {
        return (self.response() != null);
    });

    self.api_example = ko.observable(null);
}

module.exports.init_embed = function (config) {
    // Update embed view with manually populated select
    var view = new EmbedView(config);
    ko.applyBindings(view, $('#tool-embed')[0]);
}

if (typeof(window) != 'undefined') {
    window.tools = module.exports;
}

/*
      function showHelp() {
        ReadTheDocs.embed.into('docs', 'versions', 'How we envision versions working', function (data) {
          $("#id_help").html(data['content'])
          $('#id_help').toggle()
        })
      }
*/
