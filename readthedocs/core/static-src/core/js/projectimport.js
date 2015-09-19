var ko = require('knockout'),
    $ = require('jquery'),
    tasks = require('./tasks');

require('./django-csrf.js');


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

  $('[data-sync-repositories]').each(function () {

    function onSuccess(url) {
      $.ajax({
        method: 'GET',
        url: window.location.href,
        success: function (data) {
          var $newContent = $(data).find(target);
          $('body').find(target).replaceWith($newContent);
          $('.sync-repositories').addClass('hide');
          $('.sync-repositories-progress').addClass('hide');
          $('.sync-repositories-success').removeClass('hide');
        },
        error: onError
      });
    }
  });
});

function Organization (instance) {
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
}

function Project (instance) {
    var self = this;
    self.id = ko.observable(instance.id);
    self.name = ko.observable(instance.name);
    self.full_name = ko.observable(instance.full_name);
    self.organization = ko.observable();
    if (instance.organization) {
        self.organization(new Organization(instance.organization));
    }
    self.http_url = ko.observable(instance.http_url);
    self.clone_url = ko.observable(instance.clone_url);
    self.ssh_url = ko.observable(instance.ssh_url);
    self.private = ko.observable(instance.private);
    self.active = ko.observable(instance.active);
    self.avatar_url = ko.observable(
        append_url_params(instance.avatar_url, {size: 32})
    );

    self.import_repo = function () {
        alert('FUCK');
    };
}

function ProjectImportView (instance, urls) {
    var self = this,
        instance = instance || {};

    self.urls = urls || {};

    // For task display
    self.error = ko.observable(null);
    self.is_syncing = ko.observable(false);

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
            var organization = new Organization(organizations_raw[n]);
            organizations.push(organization);
        }
        return organizations;
    });
    self.projects = ko.observableArray()

    ko.computed(function () {
        var org = self.filter_org(),
            orgs = self.organizations(),
            url = self.page_current() || self.urls['oauthrepository-list'];

        if (org) {
            url = append_url_params(url, {org: org});
        }

        $.getJSON(url)
            .success(function (projects_list) {
                var projects = [];
                self.page_next(projects_list.next);
                self.page_previous(projects_list.previous);

                for (n in projects_list.results) {
                    // TODO replace org id here
                    var project = new Project(projects_list.results[n]);
                    projects.push(project);
                }
                self.projects(projects);
            })
            .error(function (error) {
                self.error(error);
            });
    });

    self.get_organizations = function () {
        $.getJSON(self.urls['oauthorganization-list'])
            .success(function (organizations) {
                self.organizations_raw(organizations.results);
            })
            .error(function (error) {
                self.error(error);
            });
    };

    self.sync_projects = function () {
        var url = self.urls.api_sync_github_repositories;

        self.error(null);
        self.is_syncing(true);

        tasks.trigger_task(url)
            .then(function (data) {
                self.get_organizations();
            })
            .fail(function (error) {
                error = error || 'An error occured';
                self.error(error);
            })
            .always(function () {
                self.is_syncing(false);
            })
    }

    self.next_page = function () {
        self.page_current(self.page_next());
    }

    self.previous_page = function () {
        self.page_current(self.page_previous());
    }
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

ProjectImportView.init = function (domobj, instance, urls) {
    var view = new ProjectImportView(instance, urls);
    view.get_organizations();
    ko.applyBindings(view, domobj);
    return view;
};

module.exports.ProjectImportView = ProjectImportView;
