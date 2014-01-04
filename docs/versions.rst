Versions
========

Read the Docs supports multiple versions of your repository.
On the initial import,
we will create a ``latest`` version.
This will point at the default branch for your VCS control: ``master``, ``default``, or ``trunk``.

How we envision versions working
--------------------------------

In the normal case,
the ``latest`` version will always point to the most up to date development code.
If you develop on a branch that is different than the default for your VCS,
you should set the **Default Branch** to that branch.

You should push a **tag** for each version of your project.
These tags should be numbered in a way that is consistent with `semantic versioning <http://semver.org/>`_.

If you have documentation changes on a long-lived **branch**,
you can build those too.
This will allow you to see how the new docs will be built in this branch of the code.
Generally you won't have more than 1 active branch over a long period of time.
The main exception here would be *release branches*,
which are branches that are maintained over time for a specific release number.

Redirects on root URLs
----------------------

When a user hits the root URL for your documentation,
for example ``http://pip.readthedocs.org/``,
they will be redirected to the **Default verison**.
This defaults to **latest**,
but could also point to your latest released version.


