// Donate payment views

var jquery = require('jquery'),
    payment = require('readthedocs/payments/static-src/payments/js/base'),
    ko = require('knockout');

function DonateView (config) {
    var self = this,
        config = config || {};

    self.constructor.call(self, config);

    self.dollars_select = ko.observable();
    self.dollars_input = ko.observable();
    self.dollars = ko.computed(function () {
        var dollars;
        dollars = self.dollars_select();
        if (dollars == 'custom') {
           dollars = self.dollars_input();
        }
        return dollars;
    });
    self.logo_url = ko.observable();
    self.site_url = ko.observable();
    self.error_dollars = ko.observable();
    self.error_logo_url = ko.observable();
    self.error_site_url = ko.observable();

    ko.computed(function () {
        var input_logo = $('input#id_logo_url').closest('p'),
            input_site = $('input#id_site_url').closest('p');
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

DonateView.prototype = new payment.PaymentView();

DonateView.init = function (config, obj) {
    var view = new DonateView(config),
        obj = obj || $('#donate-payment')[0];
    ko.applyBindings(view, obj);
    return view;
}

DonateView.prototype.submit_form = function (card_digits, token) {
    this.form.find('#id_last_4_digits').val(card_digits);
    this.form.find('#id_stripe_token').val(token);
    this.form.submit();
};

module.exports.DonateView = DonateView;
