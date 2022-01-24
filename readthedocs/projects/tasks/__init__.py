# TODO: remove this file completely
#
# We only need this file to accept tasks triggered by old web instances during
# deploy. Once it's deployed, we can delete it completely since new web
# instances will trigger the new task
# `readthedocs.projects.tasks.builds.update_docs_task` instead
#
# We may want to deploy builders first, since we will be triggering the new
# task from webs and old builders won't have it defined otherwise.


from readthedocs.worker import app

from .builds import UpdateDocsTask


@app.task(
    base=UpdateDocsTask,
    bind=True,
)
def update_docs_task(self, *args, **kwargs):
    self.request.kwargs['version_pk'] = args[0]

    # NOTE: `before_start` is new on Celery 5.2.x, but we are using 5.1.x currently.
    self.before_start(self.request.id, self.request.args, self.request.kwargs)

    self.execute()
