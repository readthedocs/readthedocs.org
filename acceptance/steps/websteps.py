
from pyquery import PyQuery as pq
import requests


@when(u'I view {url}')
def step_impl(context, url):
    context.response = requests.get(context.base_url + url)


@then(u'I should see a list of projects')
def step_impl(context):
    assert context.response.status_code == 200
    page = pq(context.response.text)
    projects = page("li.module-item")
    assert len(projects) == 14
