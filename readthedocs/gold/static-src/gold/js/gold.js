// Gold payment views

var jquery = require('jquery'),
    payment = require('readthedocs/payments/static-src/payments/js/base'),
    ko = require('knockout');

function GoldView (config) {
    var self = this,
        config = config || {};

    self.constructor.call(self, config);

    self.last_4_digits = ko.observable(null);
}

GoldView.prototype = new payment.PaymentView();

GoldView.init = function (config, obj) {
    var view = new GoldView(config),
        obj = obj || $('#payment-form')[0];
    ko.applyBindings(view, obj);
    return view;
}

GoldView.prototype.submit_form = function (card_digits, token) {
    this.form.find('#id_last_4_digits').val(card_digits);
    this.form.find('#id_stripe_token').val(token);
    this.form.submit();
};

module.exports.GoldView = GoldView;
