function StripeCheckoutView(config) {
    var self = this;
    var config = config || {};

    self.stripe = Stripe(config.stripeKey);
    self.formId = config.formId || '';
    self.levelId = config.levelId || '';
    self.checkoutSessionUrl = config.checkoutSessionUrl || '';
    self.csrfToken = config.csrfToken || '';

    self.initForm = function () {
        document
            .getElementById(self.formId)
            .addEventListener("click", function (event) {
                // Avoid submitting the form
                event.preventDefault();

                self.createCheckoutSession().then(function (result) {
                    // Call Stripe.js method to redirect to the new Checkout page
                    result.json().then(function (data) {
                        self.stripe
                            .redirectToCheckout({
                                sessionId: data.session_id
                            });
                    });
                });
            });
    };

    self.createCheckoutSession = function () {
        var priceId = document.getElementById(self.levelId).value;
        // One-time donation fields
        var name = document.getElementById('id_name').value;
        var email = document.getElementById('id_email').value;
        var logoUrl = document.getElementById('id_logo_url').value;
        var siteUrl = document.getElementById('id_site_url').value;
        var public = document.getElementById('id_public').checked;

        return fetch(self.checkoutSessionUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": self.csrfToken
            },
            body: JSON.stringify({
                priceId: priceId,
                name: name,
                email: email,
                logoUrl: logoUrl,
                siteUrl: siteUrl,
                public: public,
            })
        });
    };
}


StripeCheckoutView.init = function (config) {
    var view = new StripeCheckoutView(config);
    view.initForm();
    return view;
};

module.exports.StripeCheckoutView = StripeCheckoutView;
