from django.urls import path

from readthedocs.oauth.views import GitHubAppWebhookView


urlpatterns = [
    path("githubapp/", GitHubAppWebhookView.as_view(), name="github_app_webhook"),
]
