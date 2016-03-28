import django.dispatch

footer_response = django.dispatch.Signal(providing_args=["context", "response_data"])
