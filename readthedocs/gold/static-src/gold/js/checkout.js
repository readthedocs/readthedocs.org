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
        var name = document.getElementById('id_name');
        var email = document.getElementById('id_email');
        var logoUrl = document.getElementById('id_logo_url');
        var siteUrl = document.getElementById('id_site_url');
        var public = document.getElementById('id_public');

        return fetch(self.checkoutSessionUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": self.csrfToken
            },
            body: JSON.stringify({
                priceId: priceId,
                name: name ? name.value : null,
                email: email ? email.value : null,
                logoUrl: logoUrl ? logoUrl.value : null,
                siteUrl: siteUrl ? siteUrl.value : null,
                public: public ? public.checked : null,
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
