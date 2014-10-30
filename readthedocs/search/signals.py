import django.dispatch

before_project_search = django.dispatch.Signal(providing_args=["body"])
before_file_search = django.dispatch.Signal(providing_args=["body"])
