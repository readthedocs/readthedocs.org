Overview of issue labels
========================

Here is a full list of labels that we use in the `GitHub issue tracker`_ and
what they stand for.

.. _GitHub issue tracker: https://github.com/rtfd/readthedocs.org/issues

*Accepted*
    Issues with this label are issues that the core team has accepted on to the
    roadmap. The core team focuses on accepted bugs, features, and improvements
    that are on our immediate roadmap and will give priority to these issues.
    Pull requests could be delayed or closed if the pull request doesn't align
    with our current roadmap. An issue or pull request that has not been
    accepted should either eventually move to an accepted state, or should be
    closed. As an issue is accepted, we will find room for it on our roadmap,
    either on an upcoming release (point release milestones), or on a future
    milestone project (named milestones).

*Bug*
    An issue describing unexpected or malicious behaviour of the readthedocs.org
    software. A Bug issue differs from an Improvement issue in that Bug issues
    are given priority on our roadmap. On release, these issues generally only
    warrant incrementing the patch level version.

*Design*
    Issues related to the UI of the readthedocs.org website.

*Feature*
    Issues that describe new features. Issues that do not describe new features,
    such as code cleanup or fixes that are not related to a bug, should probably
    be given the Improvement label instead. On release, issues with the Feature
    label warrant at least a minor version increase.

*Good First Issue*
    This label marks issues that are easy to get started with. The issue
    should be ideal for beginners to dive into the code base.

*Priority: high*
    Issues with this label should be resolved as quickly as possible.

*Priority: low*
    Issues with this label won't have the immediate focus of the core team.

*Improvement*
    An issue with this label is not a Bug nor a Feature. Code cleanup or small
    changes to existing features would likely have this label. The distinction
    for this label is that these issues have a lower priority on our roadmap
    compared to issues labeled Bug, and aren't implementing new features, such
    as a Feature issue might.

*Needed: design decision*
    Issues that need a design decision are blocked for development until a
    project leader clarifies the way in which the issue should be approached.

*Needed: documentation*
    If an issue involves creating or refining documentation, this label will be
    assigned.

*Needed: more information*
    This label indicates that a reply with more information is required from the
    bug reporter. If no response is given by the reporter, the issue is
    considered invalid after 2 weeks and will be closed. See the documentation
    about our :ref:`triage process <triage-not-enough-information>` for more
    information.

*Needed: patch*
    This label indicates that a patch is required in order to resolve the
    issue. A fix should be proposed via a pull request on GitHub.

*Needed: tests*
    This label indicates that a better test coverage is required to resolve
    the issue. New tests should be proposed via a pull request on GitHub.

*Needed: replication*
    This label indicates that a bug has been reported, but has not been
    successfully replicated by another user or contributor yet.

*Operations*
    Issues that require changes in the server infrastructure.

*PR: work in progress*
    Pull Requests that are not complete yet. A final review is not possible
    yet, but every Pull Request is open for discussion.

*PR: hotfix*
    Pull request was applied directly to production after a release. These pull
    requests still need review to be merged into the next release.

*Sprintable*
    Sprintable are all issues that have the right amount of scope to be
    handled during a sprint. They are very focused and encapsulated.

*Status: blocked*
    The issue cannot be resolved until some other issue has been closed.
    See the issue's log for which issue is blocking this issue.

*Status: stale*
    A issue is stale if it there has been no activity on it for 90 days. Once a
    issue is determined to be stale, it will be closed after 2 weeks unless
    there is activity on the issue.

*Support*
    Questions that needs answering but do not require code changes or issues
    that only require a one time action on the server will have this label.
    See the documentation about our :ref:`triage process
    <triage-support-tickets>` for more information.
