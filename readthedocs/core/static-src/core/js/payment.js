// Stripe payment form views

var ko = require('knockout'),
    payment = require('jquery.payment'),
    $ = null,
    stripe = null;

if (typeof(window) == 'undefined') {
    $ = require('jquery');
}
else {
    $ = window.$;
}


// TODO stripe doesn't support loading locally very well, do they?
if (typeof(window) != 'undefined' && typeof(window.Stripe) != 'undefined') {
    stripe = window.Stripe || {};
}

function PaymentView (config) {
    var self = this,
        config = config || {};

    // Config
    stripe.publishableKey = self.stripe_key = config.key;
    self.form = config.form;

    // Credit card parameters
    self.cc_number = ko.observable(null);
    self.cc_expiry = ko.observable(null);
    self.cc_cvv = ko.observable(null);
    self.cc_error_number = ko.observable(null);
    self.cc_error_expiry = ko.observable(null);
    self.cc_error_cvv = ko.observable(null);

    // Credit card validation
    self.initialize_form();

    // Outputs
    self.error = ko.observable(null);

    // Process form inputs and send API request to Stripe. Using jquery.payment
    // for some validation, display field errors and some generic errors.
    self.process_form = function () {
        var expiry = $.payment.cardExpiryVal(self.cc_expiry()),
            card = {
                number: self.cc_number(),
                exp_month: expiry.month,
                exp_year: expiry.year,
                cvc: self.cc_cvv()
            };

        self.error(null);
        self.cc_error_number(null);
        self.cc_error_expiry(null);
        self.cc_error_cvv(null);

        if (!$.payment.validateCardNumber(card.number)) {
            self.cc_error_number('Invalid card number');
            console.log(card);
            return false;
        }
        if (!$.payment.validateCardExpiry(card.exp_month, card.exp_year)) {
            self.cc_error_expiry('Invalid expiration date');
            return false;
        }
        if (!$.payment.validateCardCVC(card.cvc)) {
            self.cc_error_cvv('Invalid security code');
            return false;
        }

        stripe.createToken(card, function(status, response) {
            if (status === 200) {
                // Update form fields that are actually sent to 
                var cc_last_digits = self.form.find('#id_last_4_digits'),
                    token = self.form.find('#id_stripe_id,#id_stripe_token');
                cc_last_digits.val(response.card.last4);
                token.val(response.id);
                self.form.submit();
            }
            else {
                self.error(response.error.message);
            }
        });
    };
}

PaymentView.prototype.initialize_form = function () {
    var cc_number = $('input#cc-number'),
        cc_cvv = $('input#cc-cvv'),
        cc_expiry = $('input#cc-expiry');

    cc_number.payment('formatCardNumber');
    cc_expiry.payment('formatCardExpiry');
    cc_cvv.payment('formatCardCVC');
};

PaymentView.init = function (config, obj) {
    var view = new GoldView(config),
        obj = obj || $('#payment-form')[0];
    ko.applyBindings(view, obj);
    return view;
}

module.exports.PaymentView = PaymentView;


if (typeof(window) != 'undefined') {
    window.payment = module.exports;
}
