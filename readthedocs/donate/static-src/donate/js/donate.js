// Donate payment views

var payment = require('../../../../core/static-src/core/js/payment'),
    ko = require('knockout');

function DonateView (config) {
    var self = this,
        config = config || {};

    ko.utils.extend(self, new payment.PaymentView(config));

    self.dollars = ko.observable();
    self.logo_url = ko.observable();
    self.site_url = ko.observable();
    ko.computed(function () {
        var input_logo = window.$('input#id_logo_url').closest('p'),
            input_site = window.$('input#id_site_url').closest('p');
        if (self.dollars() < 400) {
            self.logo_url(null);
            self.site_url(null);
            input_logo.hide();
            input_site.hide();
        }
        else {
            input_logo.show();
            input_site.show();
        }
    });
    self.urls_enabled = ko.computed(function () {
        return (self.dollars() >= 400);
    });
}

DonateView.init = function (config, obj) {
    var view = new DonateView(config),
        obj = obj || $('#donate-payment')[0];
    ko.applyBindings(view, obj);
    return view;
}

module.exports.DonateView = DonateView;

if (typeof(window) != 'undefined') {
    window.donate = module.exports;
}
