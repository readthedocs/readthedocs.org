// Gold payment views

var jquery = require('jquery');
var payment = require('readthedocs/payments/static-src/payments/js/base');
var ko = require('knockout');

function GoldView(config) {
    var self = this;
    var config = config || {};

    self.constructor.call(self, config);

    self.last_4_card_digits = ko.observable(null);
}

GoldView.prototype = new payment.PaymentView();

GoldView.init = function (config, obj) {
    var view = new GoldView(config);
    var obj = obj || $('#payment-form')[0];
    ko.applyBindings(view, obj);
    return view;
};

module.exports.GoldView = GoldView;
