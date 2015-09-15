
var rtd = require('readthedocs-client'),
    ko = require('knockout'),
    jquery = require('jquery'),
    $ = jquery;


function EmbedView (config) {
    var self = this;

    // Normalize config
    self.config = config || {};
    if (typeof(self.config.api_host) == 'undefined') {
        self.config.api_host = 'https://readthedocs.org'
    }

    self.help = ko.observable(null);
    self.error = ko.observable(null);

    self.project = ko.observable(self.config.project);
    self.file = ko.observable(null);

    self.sections = ko.observableArray();
    ko.computed(function () {
        var file = self.file();
        self.sections.removeAll();
        if (! file) {
            return;
        }
        self.help('Loading...');
        self.error(null);
        self.section(null);

        var embed = new rtd.Embed(self.config);
        embed.page(
            self.project(), 'latest', self.file(),
            function (page) {
                self.sections.removeAll();
                self.help(null);
                self.error(null);
                var sections_data = [];
                for (n in page.sections) {
                    var section = page.sections[n];
                    $.each(section, function (title, id) {
                        sections_data.push({
                            title: title,
                            id: title
                        });
                    });
                }
                self.sections(sections_data);
            },
            function (error) {
                self.help(null);
                self.error('There was a problem retrieving data from the API');
            }
        );
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
        self.help('Loading...');
        self.error(null);
        self.response(null);
        self.api_example(null);

        var embed = new rtd.Embed(self.config);
        embed.section(
            self.project(), 'latest', self.file(), self.section(),
            function (section) {
                self.help(null);
                self.error(null);
                self.api_example(
                    "var embed = Embed();\n" +
                    "embed.section(\n" +
                    "    '" + self.project() + "', 'latest', '" + self.file() + "', '" + self.section() + "',\n" +
                    "    function (section) {\n" +
                    "        section.insertContent($('#help'));\n" +
                    "    }\n" +
                    ");\n"
                );
                self.response(section);
            },
            function (error) {
                self.help(null);
                self.error('There was a problem retrieving data from the API');
            }
        );
    });

    self.has_response = ko.computed(function () {
        return (self.response() != null);
    });

    self.api_example = ko.observable(null);

    self.show_help = function () {
        var embed = new rtd.Embed();
        embed.section(
            'docs', 'latest', 'features/embed', 'Content Embedding',
            _show_modal
        );
    };

    self.show_embed = function () {
        var embed = new rtd.Embed();
        _show_modal(self.response());
    };
}

module.exports.init_embed = function (config) {
    var view = new EmbedView(config);
    ko.applyBindings(view, $('#tool-embed')[0]);
}

// Analytics
function AnalyticsView (config) {
    var self = this;

    // Normalize config
    self.config = config || {};
    if (typeof(self.config.api_host) == 'undefined') {
        self.config.api_host = 'https://readthedocs.org'
    }

    self.show_help = function () {
        var embed = new rtd.Embed();
        embed.section(
            'docs', 'latest', 'business/analytics', 'Analytics',
            _show_modal
        );
    };
}

module.exports.init_analytics = function (config) {
    var view = new AnalyticsView(config);
    ko.applyBindings(view, $('#tool-analytics')[0]);
}

// Modal display
function _show_modal (section) {
    var embed_container = $('#embed-container');
    if (!embed_container.length) {
        embed_container = $('<div id="embed-container" class="modal modal-help" />');
        $('body').append(embed_container);
    }

    // Add iframe
    var iframe = section.insertContent(embed_container);
    $(iframe).show();
    embed_container.show();

    // Handle click out of modal
    $(document).click(function (ev) {
        if(!$(ev.target).closest('#embed-container').length) {
            $(iframe).remove();
            embed_container.remove();
        }
    });
}
