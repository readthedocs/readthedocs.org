"""We define custom Django signals to trigger when a footer is rendered."""

import django.dispatch


footer_response = django.dispatch.Signal(
    providing_args=['request', 'context', 'response_data'],
)
