// Stripe payment form views

var ko = require('knockout'),
    payment = require('jquery.payment'),
    $ = require('jquery'),
    stripe = null;

// TODO stripe doesn't support loading locally very well, do they?
if (typeof(window) != 'undefined' && typeof(window.Stripe) != 'undefined') {
    stripe = window.Stripe || {};
}

/* Knockout binding to set initial observable values from HTML */
ko.bindingHandlers.valueInit = {
    init: function(element, accessor) {
        var value = accessor();
        if (ko.isWriteableObservable(value)) {
            value(element.value);
        }
    }
};

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
    self.error_cc_number = ko.observable(null);
    self.error_cc_expiry = ko.observable(null);
    self.error_cc_cvv = ko.observable(null);

    self.stripe_token = ko.observable(null);
    self.last_4_card_digits = ko.observable(null);

    // Form editing
    self.is_editing_card = ko.observable(false);
    self.show_card_form = ko.computed(function () {
        return (self.is_editing_card() ||
                !self.last_4_card_digits() ||
                self.cc_number() ||
                self.cc_expiry() ||
                self.cc_cvv());
    });

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
        self.error_cc_number(null);
        self.error_cc_expiry(null);
        self.error_cc_cvv(null);

        if (!$.payment.validateCardNumber(card.number)) {
            self.error_cc_number('Invalid card number');
            return false;
        }
        if (!$.payment.validateCardExpiry(card.exp_month, card.exp_year)) {
            self.error_cc_expiry('Invalid expiration date');
            return false;
        }
        if (!$.payment.validateCardCVC(card.cvc)) {
            self.error_cc_cvv('Invalid security code');
            return false;
        }

        stripe.createToken(card, function(status, response) {
            if (response.error) {
                if (response.error.type == 'card_error') {
                    var code_map = {
                        'invalid_number': self.error_cc_number,
                        'incorrect_number': self.error_cc_number,
                        'expired_card': self.error_cc_number,
                        'card_declined': self.error_cc_number,
                        'invalid_expiry_month': self.error_cc_expiry,
                        'invalid_expiry_year': self.error_cc_expiry,
                        'invalid_cvc': self.error_cc_cvv,
                        'incorrect_cvc': self.error_cc_cvv,
                    }
                    var fn = code_map[response.error.code] ||
                             self.error_cc_number;
                    fn(response.error.message);
                }
                else {
                    self.error_cc_number(response.error.message);
                }
            }
            else {
                self.submit_form(response.card.last4, response.id);
            }
        });
    };

    self.process_full_form = function () {
        if (self.show_card_form()) {
            self.process_form()
        }
        else {
            return true;
        }
    };

}

PaymentView.prototype.submit_form = function (last_4_card_digits, token) {
    this.form.find('#id_last_4_card_digits').val(last_4_card_digits);
    this.form.find('#id_stripe_token').val(token);

    // Delete all user's card information before sending them to our servers
    this.form.find('#id_cc_number').val(null);
    this.form.find('#id_cc_expiry').val(null);
    this.form.find('#id_cc_cvv').val(null);

    this.form.submit();
};

PaymentView.prototype.initialize_form = function () {
    var cc_number = $('input#id_cc_number'),
        cc_cvv = $('input#id_cc_cvv'),
        cc_expiry = $('input#id_cc_expiry');

    cc_number.payment('formatCardNumber');
    cc_expiry.payment('formatCardExpiry');
    cc_cvv.payment('formatCardCVC');

    cc_number.trigger('keyup');
};

PaymentView.init = function (config, obj) {
    var view = new PaymentView(config),
        obj = obj || $('#payment-form')[0];
    ko.applyBindings(view, obj);
    return view;
}

module.exports.PaymentView = PaymentView;
