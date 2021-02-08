function StripeCheckoutView(config) {
    var self = this;
    var config = config || {};

    self.stripe = Stripe(config.stripeKey)
    self.formId = config.formId || '';
    self.levelId = config.levelId || '';
    self.checkoutSessionUrl = config.checkoutSessionUrl || '';
    self.csrfToken = config.csrfToken || '';

    self.initForm = function() {
        document
            .getElementById(self.formId)
            .addEventListener("click", function(event) {
                // Avoid submitting the form
                event.preventDefault();

                var priceId = document.getElementById(self.levelId).value;
                self.createCheckoutSession(priceId).then(function(result) {
                    // Call Stripe.js method to redirect to the new Checkout page
                    result.json().then(function(data) {
                        self.stripe
                            .redirectToCheckout({
                                sessionId: data.session_id
                            })
                    });
                });
            });
    };

    self.createCheckoutSession = function(priceId) {
        return fetch(self.checkoutSessionUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken":self.csrfToken
            },
            body: JSON.stringify({
                priceId: priceId
            })
        });
    };
};


StripeCheckoutView.init = function(config) {
    var view = new StripeCheckoutView(config);
    view.initForm();
    return view;
};

module.exports.StripeCheckoutView = StripeCheckoutView;
