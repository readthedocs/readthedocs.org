// Gold payment views

var payment = require('../../../../core/static-src/core/js/payment'),
    ko = require('knockout');

function GoldView (config) {
    var self = this,
        config = config || {};

    ko.utils.extend(self, new payment.PaymentView(config));
}

GoldView.init = function (config, obj) {
    var view = new GoldView(config),
        obj = obj || $('#payment-form')[0];
    ko.applyBindings(view, obj);
    return view;
}

module.exports.GoldView = GoldView;


if (typeof(window) != 'undefined') {
    window.payment = module.exports;
}
