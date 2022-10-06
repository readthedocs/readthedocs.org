# Avoid signature verification.
@mock.patch.object(stripe.WebhookSignature, 'verify_header', new=mock.MagicMock)
@override_settings(
    STRIPE_WEBHOOK_SECRET="1234",
    RTD_ORG_DEFAULT_STRIPE_PRICE="trialing",
)
class StripeTests(TestCase):

    """Tests for Stripe API endpoint."""

    def setUp(self):
        self.organization = fixture.get(Organization, slug='org')
        fixture.get(
            Plan,
            stripe_id='trialing',
            slug='trialing',
        )
        fixture.get(
            Plan,
            stripe_id='basic',
        )
        fixture.get(
            Plan,
            stripe_id='advanced',
        )

    def test_subscription_updated_event(self):
        """Test handled event."""

        payload = """
        {
            "id": "evt_197I3KKFrzSMUWUvE44wEYfC",
            "object": "event",
            "api_version": "2016-07-06",
            "created": 1477114098,
            "data": {
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                    "application_fee_percent": null,
                    "cancel_at_period_end": false,
                    "canceled_at": null,
                    "created": 1476137811,
                    "current_period_end": 1479792497,
                    "current_period_start": 1477114097,
                    "customer": "cus_9LtsPRYe4yJSOQ",
                    "discount": null,
                    "ended_at": null,
                    "livemode": false,
                    "metadata": {
                    },
                    "items": {
                        "object": "list",
                        "data": [
                            {
                                "id": "si_KMl5ZOLb8CzMyM",
                                "object": "subscription_item",
                                "billing_thresholds": null,
                                "created": 1633632209,
                                "metadata": {},
                                "price": {
                                    "id": "advanced",
                                    "object": "price",
                                    "unit_amount": 1500,
                                    "unit_amount_decimal": "1500",
                                    "created": 1475279464,
                                    "currency": "usd",
                                    "recurring": {
                                        "aggregate_usage": null,
                                        "interval": "month",
                                        "interval_count": 1,
                                        "trial_period_days": 30,
                                        "usage_type": "licensed"
                                    },
                                    "livemode": false,
                                    "metadata": {
                                    }
                                }
                            }
                        ]
                    },
                    "quantity": 1,
                    "start_date": 1477114097,
                    "status": "active",
                    "tax_percent": null,
                    "trial_end": null,
                    "trial_start": null
                },
                "previous_attributes": {
                    "current_period_end": 1478733360,
                    "current_period_start": 1476137811,
                    "start_date": 1476137811,
                    "status": "active",
                    "trial_end": 1478733360,
                    "trial_start": 1476137811
                }
            },
            "livemode": false,
            "pending_webhooks": 0,
            "request": "req_9Q8JSVL19hmjmN",
            "type": "customer.subscription.updated"
        }
        """
        subscription = fixture.get(
            Subscription, stripe_id='sub_9LtsU02uvjO6Ed',
            status='trialing',
        )
        client = APIClient()
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['updated'], True)
        self.assertEqual(resp.data['subscription_id'], 'sub_9LtsU02uvjO6Ed')
        subscription = Subscription.objects.get(stripe_id='sub_9LtsU02uvjO6Ed')
        self.assertEqual(subscription.status, 'active')
        self.assertIsNotNone(subscription.trial_end_date)
        self.assertEqual(subscription.end_date.timestamp(), 1479792497.0)

    def test_unhandled_event(self):
        """Test unhandled event."""

        payload = """
        {
            "id": "evt_197I3KKFrzSMUWUvE44wEYfC",
            "object": "event",
            "api_version": "2016-07-06",
            "created": 1477114098,
            "data": {
                "object": {}
            },
            "livemode": false,
            "pending_webhooks": 0,
            "request": "req_9Q8JSVL19hmjmN",
            "type": "account.updated"
        }
        """

        subscription = fixture.get(
            Subscription, stripe_id='sub_9LtsU02uvjO6Ed',
            status='trialing',
        )
        client = APIClient()
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reenabled_organization_on_subscription_updated_event(self):
        """Organization is re-enabled when subscription is active."""

        payload = """
        {
            "id": "evt_197I3KKFrzSMUWUvE44wEYfC",
            "object": "event",
            "api_version": "2016-07-06",
            "created": 1477114098,
            "data": {
                "object": {
                    "id": "sub_9LtsU02uvjO6Ed",
                    "object": "subscription",
                    "application_fee_percent": null,
                    "cancel_at_period_end": false,
                    "canceled_at": null,
                    "created": 1476137811,
                    "current_period_end": 1479792497,
                    "current_period_start": 1477114097,
                    "customer": "cus_9LtsPRYe4yJSOQ",
                    "discount": null,
                    "ended_at": null,
                    "livemode": false,
                    "metadata": {
                    },
                    "items": {
                        "object": "list",
                        "data": [
                            {
                                "id": "si_KMl5ZOLb8CzMyM",
                                "object": "subscription_item",
                                "billing_thresholds": null,
                                "created": 1633632209,
                                "metadata": {},
                                "price": {
                                    "id": "advanced",
                                    "object": "price",
                                    "unit_amount": 1500,
                                    "unit_amount_decimal": "1500",
                                    "created": 1475279464,
                                    "currency": "usd",
                                    "recurring": {
                                        "aggregate_usage": null,
                                        "interval": "month",
                                        "interval_count": 1,
                                        "trial_period_days": 30,
                                        "usage_type": "licensed"
                                    },
                                    "livemode": false,
                                    "metadata": {
                                    }
                                }
                            }
                        ]
                    },
                    "quantity": 1,
                    "start_date": 1477114097,
                    "status": "active",
                    "tax_percent": null,
                    "trial_end": null,
                    "trial_start": null
                },
                "previous_attributes": {
                    "current_period_end": 1478733360,
                    "current_period_start": 1476137811,
                    "start_date": 1476137811,
                    "status": "active",
                    "trial_end": 1478733360,
                    "trial_start": 1476137811
                }
            },
            "livemode": false,
            "pending_webhooks": 0,
            "request": "req_9Q8JSVL19hmjmN",
            "type": "customer.subscription.updated"
        }
        """

        organization = fixture.get(
            Organization,
            disabled=True,
        )
        subscription = fixture.get(
            Subscription,
            organization=organization,
            stripe_id='sub_9LtsU02uvjO6Ed',
            status='canceled',
        )
        client = APIClient()
        self.assertTrue(organization.disabled)
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['updated'], True)
        self.assertEqual(resp.data['subscription_id'], 'sub_9LtsU02uvjO6Ed')
        subscription = Subscription.objects.get(stripe_id='sub_9LtsU02uvjO6Ed')
        organization.refresh_from_db()
        self.assertEqual(subscription.status, 'active')
        self.assertIsNotNone(subscription.trial_end_date)
        self.assertFalse(organization.disabled)
        self.assertEqual(subscription.end_date.timestamp(), 1479792497.0)

    def test_subscription_deleted_event(self):
        payload = """
        {
            "id": "evt_1Ji1kgKFrzSMUWUv4vtbtGT9",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1633632933,
            "data": {
                "object": {
                    "id": "sub_1Ji1YyKFrzSMUWUvPghVBB66",
                    "object": "subscription",
                    "application_fee_percent": null,
                    "automatic_tax": {
                        "enabled": false
                    },
                    "billing_cycle_anchor": 1633632293,
                    "billing_thresholds": null,
                    "cancel_at": null,
                    "cancel_at_period_end": false,
                    "canceled_at": 1633632565,
                    "collection_method": "charge_automatically",
                    "created": 1633632208,
                    "current_period_end": 1636310693,
                    "current_period_start": 1633632293,
                    "customer": "cus_KMl5qf77rIpBWv",
                    "days_until_due": null,
                    "default_payment_method": "pm_1Ji1aJKFrzSMUWUv4mRVcupr",
                    "default_source": null,
                    "default_tax_rates": [],
                    "discount": null,
                    "ended_at": 1633632933,
                    "items": {
                        "object": "list",
                        "data": [
                            {
                                "id": "si_KMl5ZOLb8CzMyM",
                                "object": "subscription_item",
                                "billing_thresholds": null,
                                "created": 1633632209,
                                "metadata": {},
                                "price": {
                                    "id": "advanced",
                                    "object": "price",
                                    "active": true,
                                    "billing_scheme": "per_unit",
                                    "created": 1475279464,
                                    "currency": "usd",
                                    "livemode": false,
                                    "lookup_key": null,
                                    "metadata": {
                                        "SSO": "Single Sign-On"
                                    },
                                    "nickname": "Includes Custom Domains and more!",
                                    "product": "prod_BV0U8VTu4d8E4h",
                                    "recurring": {
                                        "aggregate_usage": null,
                                        "interval": "month",
                                        "interval_count": 1,
                                        "trial_period_days": 30,
                                        "usage_type": "licensed"
                                    },
                                    "tax_behavior": "unspecified",
                                    "tiers_mode": null,
                                    "transform_quantity": null,
                                    "type": "recurring",
                                    "unit_amount": 15000,
                                    "unit_amount_decimal": "15000"
                                },
                                "quantity": 1,
                                "subscription": "sub_1Ji1YyKFrzSMUWUvPghVBB66",
                                "tax_rates": []
                            }
                        ],
                        "has_more": false,
                        "total_count": 1,
                        "url": "/v1/subscription_items?subscription=sub_1Ji1YyKFrzSMUWUvPghVBB66"
                    },
                    "latest_invoice": "in_1Ji1d7KFrzSMUWUvIg9rpjUE",
                    "livemode": false,
                    "metadata": {},
                    "next_pending_invoice_item_invoice": null,
                    "pause_collection": null,
                    "payment_settings": {
                        "payment_method_options": null,
                        "payment_method_types": null
                    },
                    "pending_invoice_item_interval": null,
                    "pending_setup_intent": null,
                    "pending_update": null,
                    "quantity": 1,
                    "schedule": null,
                    "start_date": 1633632208,
                    "status": "canceled",
                    "transfer_data": null,
                    "trial_end": 1633632292,
                    "trial_start": 1633632208
                }
            },
            "livemode": false,
            "pending_webhooks": 3,
            "request": {
                "id": "req_LltV9EVcHShY68",
                "idempotency_key": null
            },
            "type": "customer.subscription.deleted"
        }
        """
        subscription = fixture.get(
            Subscription,
            organization=self.organization,
            stripe_id='sub_1Ji1YyKFrzSMUWUvPghVBB66',
            status='active',
        )
        client = APIClient()
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['updated'], True)
        self.assertIsNone(resp.data['subscription_id'])
        self.assertEqual(resp.data['previous_subscription_id'], 'sub_1Ji1YyKFrzSMUWUvPghVBB66')
        subscription.refresh_from_db()
        self.assertIsNone(subscription.stripe_id)
        self.assertEqual(subscription.status , 'canceled')

    @mock.patch.object(stripe.Subscription, 'retrieve')
    def test_subscription_checkout_completed_event(self, subscription_retrieve_mock):
        payload = """
        {
            "id": "evt_1Ji12qKFrzSMUWUvnGxsOJEd",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1633630215,
            "data": {
                "object": {
                    "id": "cs_test_a1UpM7pDdpXqqgZC6lQDC2HRMo5d1wW9fNX0ZiBCm6vRqTgZJZx6brwNan",
                    "object": "checkout.session",
                    "after_expiration": null,
                    "allow_promotion_codes": null,
                    "amount_subtotal": 5000,
                    "amount_total": 5000,
                    "automatic_tax": {
                        "enabled": false,
                        "status": null
                    },
                    "billing_address_collection": null,
                    "cancel_url": "http://6c9f-186-66-172-152.ngrok.io/organizations/foo/subscription/",
                    "client_reference_id": null,
                    "consent": null,
                    "consent_collection": null,
                    "currency": "usd",
                    "customer": "cus_KMiHJXFHpLkcRP",
                    "customer_details": {
                        "email": "admin@admin.com",
                        "tax_exempt": "none",
                        "tax_ids": []
                    },
                    "customer_email": null,
                    "expires_at": 1633716598,
                    "livemode": false,
                    "locale": null,
                    "metadata": {},
                    "mode": "subscription",
                    "payment_intent": null,
                    "payment_method_options": {},
                    "payment_method_types": [
                        "card"
                    ],
                    "payment_status": "paid",
                    "recovered_from": null,
                    "setup_intent": "seti_1Ji12mKFrzSMUWUvMrvmajcF",
                    "shipping": null,
                    "shipping_address_collection": null,
                    "submit_type": null,
                    "subscription": "sub_9LtsU02uvjO6Ed",
                    "success_url": "http://6c9f-186-66-172-152.ngrok.io/organizations/foo/subscription/?upgraded=true",
                    "total_details": {
                        "amount_discount": 0,
                        "amount_shipping": 0,
                        "amount_tax": 0
                    },
                    "url": null
                }
            },
            "livemode": false,
            "pending_webhooks": 5,
            "request": {
                "id": null,
                "idempotency_key": null
            },
            "type": "checkout.session.completed"
        }
        """

        self.organization.stripe_id = 'cus_KMiHJXFHpLkcRP'
        self.organization.save()
        subscription_retrieve_mock.return_value = stripe.Subscription.construct_from(
            values={
                "id": "sub_9LtsU02uvjO6Ed",
                "canceled_at": None,
                "created": 1476137811,
                "current_period_end": 1479792497,
                "current_period_start": 1477114097,
                "customer": "cus_KMiHJXFHpLkcRP",
                "items": {
                    "object": "list",
                    "data": [
                        {
                            "id": "si_KOcEsHCktPUedU",
                            "object": "subscription_item",
                            "price": {
                                "id": "advanced",
                                "object": "price",
                                "unit_amount": 1500,
                                "unit_amount_decimal": "1500",
                                "created": 1475279464,
                                "currency": "usd",
                                "recurring": {
                                    "aggregate_usage": None,
                                    "interval": "month",
                                    "interval_count": 1,
                                    "trial_period_days": 30,
                                    "usage_type": "licensed",
                                },
                            },
                        }
                    ],
                },
                "start_date": 1477114097,
                "status": "active",
                "trial_end": None,
                "trial_start": None,
            },
            key=None,
        )
        subscription = fixture.get(
            Subscription,
            organization=self.organization,
            stripe_id=None,
            status='canceled',
        )
        client = APIClient()
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['updated'], True)
        self.assertEqual(resp.data['subscription_id'], 'sub_9LtsU02uvjO6Ed')
        self.assertEqual(resp.data['previous_subscription_id'], None)
        subscription.refresh_from_db()
        self.assertEqual(subscription.stripe_id, 'sub_9LtsU02uvjO6Ed')
        self.assertEqual(subscription.status , 'active')

    @mock.patch('readthedocsinc.api.v2.views.cancel_subscription')
    def test_cancel_subscription_after_trial_has_ended(self, cancel_subscription_mock):
        payload = """
        {
            "id": "evt_1Jjp3aKFrzSMUWUvIfMwnfw3",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1634060789,
            "data": {
                "object": {
                    "id": "sub_1JjozxKFrzSMUWUvkgpVXQt8",
                    "object": "subscription",
                    "application_fee_percent": null,
                    "automatic_tax": {
                        "enabled": false
                    },
                    "billing_cycle_anchor": 1634060789,
                    "billing_thresholds": null,
                    "cancel_at": null,
                    "cancel_at_period_end": false,
                    "canceled_at": null,
                    "collection_method": "charge_automatically",
                    "created": 1634060565,
                    "current_period_end": 1636739189,
                    "current_period_start": 1634060789,
                    "customer": "cus_KOcEOz4gd3lN8X",
                    "days_until_due": null,
                    "default_payment_method": null,
                    "default_source": null,
                    "default_tax_rates": [
                    ],
                    "discount": null,
                    "ended_at": null,
                    "items": {
                        "object": "list",
                        "data": [
                        {
                            "id": "si_KOcEsHCktPUedU",
                            "object": "subscription_item",
                            "billing_thresholds": null,
                            "created": 1634060565,
                            "metadata": {
                            },
                            "price": {
                            "id": "trialing",
                            "object": "price",
                            "active": true,
                            "billing_scheme": "per_unit",
                            "created": 1629733210,
                            "currency": "usd",
                            "livemode": false,
                            "lookup_key": null,
                            "metadata": {
                            },
                            "nickname": null,
                            "product": "prod_K1qnUPyioLO51V",
                            "recurring": {
                                "aggregate_usage": null,
                                "interval": "month",
                                "interval_count": 1,
                                "trial_period_days": 30,
                                "usage_type": "licensed"
                            },
                            "tax_behavior": "unspecified",
                            "tiers_mode": null,
                            "transform_quantity": null,
                            "type": "recurring",
                            "unit_amount": 0,
                            "unit_amount_decimal": "0"
                            },
                            "quantity": 1,
                            "subscription": "sub_1JjozxKFrzSMUWUvkgpVXQt8",
                            "tax_rates": [
                            ]
                        }
                        ],
                        "has_more": false,
                        "total_count": 1,
                        "url": "/v1/subscription_items?subscription=sub_1JjozxKFrzSMUWUvkgpVXQt8"
                    },
                    "latest_invoice": "in_1Jjp3ZKFrzSMUWUvN9pqY3ub",
                    "livemode": false,
                    "metadata": {
                    },
                    "next_pending_invoice_item_invoice": null,
                    "pause_collection": null,
                    "payment_settings": {
                        "payment_method_options": null,
                        "payment_method_types": null
                    },
                    "pending_invoice_item_interval": null,
                    "pending_setup_intent": "seti_1JjozxKFrzSMUWUvTmU4SztV",
                    "pending_update": null,
                    "quantity": 1,
                    "schedule": null,
                    "start_date": 1634060565,
                    "status": "active",
                    "transfer_data": null,
                    "trial_end": 1634060788,
                    "trial_start": 1634060565
                },
                "previous_attributes": {
                    "billing_cycle_anchor": 1636652565,
                    "current_period_end": 1636652565,
                    "current_period_start": 1634060565,
                    "latest_invoice": "in_1JjozxKFrzSMUWUvhLCv0xy9",
                    "status": "trialing",
                    "trial_end": 1636652565
                }
            },
            "livemode": false,
            "pending_webhooks": 3,
            "request": {
                "id": "req_dloiXHqk7BR4rQ",
                "idempotency_key": null
            },
            "type": "customer.subscription.updated"
        }
        """
        subscription = fixture.get(
            Subscription,
            organization=self.organization,
            stripe_id='sub_1JjozxKFrzSMUWUvkgpVXQt8',
            status='active',
        )
        self.organization.stripe_id = 'cus_KMiHJXFHpLkcRP'
        self.organization.save()
        client = APIClient()
        resp = client.post(
            '/api/v2/stripe/',
            json.loads(payload),
            format='json',
            HTTP_STRIPE_SIGNATURE='',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['updated'], True)
        self.assertEqual(resp.data['subscription_id'], 'sub_1JjozxKFrzSMUWUvkgpVXQt8')
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.is_trial_ended)
        cancel_subscription_mock.assert_called_once_with("sub_1JjozxKFrzSMUWUvkgpVXQt8")
