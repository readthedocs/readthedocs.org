"""Tasks related to telemetry."""

from readthedocs.builds.models import Build
from readthedocs.telemetry.models import BuildData
from readthedocs.worker import app


@app.task(queue="web")
def save_build_data(build_id, data):
    """
    Save the build data asynchronously.

    Mainly used from the builders,
    since they don't have access to the database.
    """
    build = Build.objects.filter(id=build_id).first()
    if build:
        BuildData.objects.collect(build, data)
