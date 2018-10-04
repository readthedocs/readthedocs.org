Roadmap
=======

Process
-------

Read the Docs has adopted the following workflow with regards to how we
prioritize our development efforts and where the core development team focuses
its time.

Triaging issues
~~~~~~~~~~~~~~~

Much of this is already covered in our guide on :doc:`contribute`, however to
summarize the important pieces:

* New issues coming in will be triaged, but won't yet be considered part of our
  roadmap.
* If the issue is a valid bug, it will be assigned the ``Accepted`` label and
  will be prioritized, likely on an upcoming point release.
* If the issues is a feature or improvement, the issue might go through a design
  decision phase before being accepted and assigned to a milestone. This is a
  good time to discuss how to address the problem technically. Skipping this
  phase might result in your PR being blocked, sent back to design decision, or
  perhaps even discarded. It's best to be active here before submitting a PR for
  a feature or improvement.
* The core team will only work on accepted issues, and will give PR review
  priority to accepted issues. Pull requests addressing issues that are not on
  our roadmap are welcome, but we cannot guarantee review response, even for
  small or easy to review pull requests.

Milestones
~~~~~~~~~~

We maintain two types of milestones: point release milestones for our upcoming
releases, and group milestones, for blocks of work that have priority in the
future.

Generally there are 2 or 3 point release milestones lined up. These point
releases dictate the issues that core team has discussed as priority already.
Core team should not focus on issues outside these milestones as that implies
either the issue was not discussed as a priority, or the issue isn't a priority.

We follow `semantic versioning`_ for our release numbering and our point release
milestones follow these guidelines. For example, our next release milestones
might be ``2.8``, ``2.9``, and ``3.0``. Releases ``2.8`` and ``2.9`` will
contain bug fix issues and one backwards compatible feature (this dictates the
change in minor verison). Release ``3.0`` will contain bugfixes and at least one
backwards incompatible change.

Point release milestones try to remain static, but can shift upwards on a
release that included an unexpected feature addition. Sometimes the resulting PR
unexpectedly includes changes that dictate a minor version increment though,
according to `semantic versioning`_. In this case, the current milestone is
closed, future milestones are increased a minor point if necessary, and the
remaining milestone issues are migrated to a new milestone for the next upcoming
release number.

Group milestones are blocks of work that will have priority in the future, but
aren't included on point releases yet. When the core team does decide to make
these milestones a priorty, they will be moved into point release milestones.

.. _semantic versioning: https://semver.org

Where to contribute
~~~~~~~~~~~~~~~~~~~

It's best to pick off an issue from our current point release or group
milestones, to ensure your pull request gets attention. You can also feel free
to contribute on our Cleanup or Refactoring milestones. Though not a development
priority, these issues are generally discrete, easier to jump into than feature
development, and we especially appreciate outside contributions here as these
milestones are not a place the core team can justify spending time in
development currently.

Current roadmap
---------------

In addition to the point release milestones currently established, our current
roadmap priorities also include:

Admin UX
    https://github.com/rtfd/readthedocs.org/milestone/16

Search Improvements
    https://github.com/rtfd/readthedocs.org/milestone/23

YAML File Completion
    https://github.com/rtfd/readthedocs.org/milestone/28

There are also several milestones that are explicitly *not* a priority for the
core team:

Cleanup
    https://github.com/rtfd/readthedocs.org/milestone/10

Refactoring
    https://github.com/rtfd/readthedocs.org/milestone/34

Core team will not be focusing their time on these milestones in development.
