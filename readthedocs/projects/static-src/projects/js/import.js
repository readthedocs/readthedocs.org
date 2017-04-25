var ko = require('knockout'),
    $ = require('jquery'),
    tasks = require('readthedocs/core/static-src/core/js/tasks');


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
});

function Organization (instance, view) {
    var self = this;
    self.id = ko.observable(instance.id);
    self.name = ko.observable(instance.name);
    self.slug = ko.observable(instance.slug);
    self.active = ko.observable(instance.active);
    self.avatar_url = ko.observable(
        append_url_params(instance.avatar_url, {size: 32})
    );
    self.display_name = ko.computed(function () {
        return self.name() || self.slug();
    });
    self.filtered = ko.computed(function () {
        var id = view.filter_org();
        return id && id != self.id();
    });
}

function Project (instance, view) {
    var self = this;
    self.id = ko.observable(instance.id);
    self.name = ko.observable(instance.name);
    self.full_name = ko.observable(instance.full_name);
    self.description = ko.observable(instance.description);
    self.vcs = ko.observable(instance.vcs);
    self.organization = ko.observable();
    self.html_url = ko.observable(instance.html_url);
    self.clone_url = ko.observable(instance.clone_url);
    self.ssh_url = ko.observable(instance.ssh_url);
    self.matches = ko.observable(instance.matches);
    self.match = ko.computed(function () {
        var matches = self.matches();
        if (matches && matches.length > 0) {
            return matches[0];
        }
    });
    self.private = ko.observable(instance.private);
    self.active = ko.observable(instance.active);
    self.admin = ko.observable(instance.admin);
    self.is_locked = ko.computed(function () {
        return (self.private() && !self.admin());
    });
    self.avatar_url = ko.observable(
        append_url_params(instance.avatar_url, {size: 32})
    );

    self.import_repo = function () {
        var data = {
                name: self.name(),
                repo: self.clone_url(),
                repo_type: self.vcs(),
                description: self.description(),
                project_url: self.html_url(),
                remote_repository: self.id(),
            },
            form = $('<form />');

        form
            .attr('action', view.urls.projects_import)
            .attr('method', 'POST')
            .hide();

        Object.keys(data).map(function (attr) {
            var field = $('<input>')
                .attr('type', 'hidden')
                .attr('name', attr)
                .attr('value', data[attr]);
            form.append(field);
        });

        var csrf_field = $('<input>')
            .attr('type', 'hidden')
            .attr('name', 'csrfmiddlewaretoken')
            .attr('value', view.csrf_token);
        form.append(csrf_field);

        // Add a button and add the form to body to satisfy Firefox
        var button = $('<input>')
            .attr('type', 'submit');
        form.append(button);
        $('body').append(form);

        form.submit();
    };
}

function ProjectImportView (instance, config) {
    var self = this,
        instance = instance || {};

    self.config = config || {};
    self.urls = config.urls || {};
    self.csrf_token = config.csrf_token || '';

    // For task display
    self.error = ko.observable(null);
    self.is_syncing = ko.observable(false);
    self.is_ready = ko.observable(false);

    // For filtering
    self.page_count = ko.observable(null);
    self.page_current = ko.observable(null);
    self.page_next = ko.observable(null);
    self.page_previous = ko.observable(null);
    self.filter_org = ko.observable(null);

    self.organizations_raw = ko.observableArray();
    self.organizations = ko.computed(function () {
        var organizations = [],
            organizations_raw = self.organizations_raw();
        for (n in organizations_raw) {
            var organization = new Organization(organizations_raw[n], self);
            organizations.push(organization);
        }
        return organizations;
    });
    self.projects = ko.observableArray();

    ko.computed(function () {
        var org = self.filter_org(),
            orgs = self.organizations(),
            url = self.page_current() || self.urls['remoterepository-list'];

        if (org) {
            url = append_url_params(
                self.urls['remoterepository-list'],
                {org: org}
            );
        }

        self.error(null);

        $.getJSON(url)
            .success(function (projects_list) {
                var projects = [];
                self.page_next(projects_list.next);
                self.page_previous(projects_list.previous);

                for (n in projects_list.results) {
                    var project = new Project(projects_list.results[n], self);
                    projects.push(project);
                }
                self.projects(projects);
            })
            .error(function (error) {
                var error_msg = error.responseJSON.detail || error.statusText;
                self.error({message: error_msg});
            })
            .always(function () {
                self.is_ready(true);
            });
    });

    self.get_organizations = function () {
        $.getJSON(self.urls['remoteorganization-list'])
            .success(function (organizations) {
                self.organizations_raw(organizations.results);
            })
            .error(function (error) {
                var error_msg = error.responseJSON.detail || error.statusText;
                self.error({message: error_msg});
            });
    };

    self.sync_projects = function () {
        var url = self.urls.api_sync_remote_repositories;

        self.error(null);
        self.is_syncing(true);

        tasks.trigger_task({url: url, token: self.csrf_token})
            .then(function (data) {
                self.get_organizations();
            })
            .fail(function (error) {
                self.error(error);
            })
            .always(function () {
                self.is_syncing(false);
            })
    };

    self.has_projects = ko.computed(function () {
        return self.projects().length > 0;
    });

    self.next_page = function () {
        self.page_current(self.page_next());
    };

    self.previous_page = function () {
        self.page_current(self.page_previous());
    };

    self.set_filter_org = function (id) {
        var current_id = self.filter_org();
        if (current_id == id) {
            id = null;
        }
        self.filter_org(id);
    };
}

function append_url_params (url, params) {
    var link = $('<a>').attr('href', url).get(0);

    Object.keys(params).map(function (key) {
        if (link.search) {
            link.search += '&';
        }
        link.search += key + '=' + params[key];
    });
    return link.href;
}

ProjectImportView.init = function (domobj, instance, config) {
    var view = new ProjectImportView(instance, config);
    view.get_organizations();
    ko.applyBindings(view, domobj);
    return view;
};

module.exports.ProjectImportView = ProjectImportView;
