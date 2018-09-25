Contributing to Read the Docs
=============================

You are here to help on Read the Docs? Awesome, feel welcome and read the
following sections in order to know how to ask questions and how to work on something. 

All members of our community are expected to follow our :doc:`/code-of-conduct`.
Please make sure you are welcoming and friendly in all of our spaces.

Get in touch
------------

- Ask usage questions ("How do I?") on `StackOverflow`_.
- Report bugs, suggest features or view the source code `on GitHub`_.
- Discuss topics on `Gitter`_.
- On IRC find us at `#readthedocs`_.

.. _StackOverFlow: https://stackoverflow.com/questions/tagged/read-the-docs
.. _on GitHub: https://github.com/rtfd/readthedocs.org
.. _Gitter: https://gitter.im/rtfd/readthedocs.org
.. _#readthedocs: irc://irc.freenode.net/readthedocs

Contributing to development
---------------------------

If you want to deep dive and help out with development on Read the Docs, then
first get the project installed locally according to the
:doc:`Installation Guide <install>`. After that is done we
suggest you have a look at tickets in our issue tracker that are labelled `Good
First Issue`_. These are meant to be a great way to get a smooth start and
won't put you in front of the most complex parts of the system.

If you are up to more challenging tasks with a bigger scope,
then there are a set of tickets with a `Feature`_ or `Improvement`_ tag.
These tickets have a general overview and description of the work required to finish.
If you want to start somewhere, this would be a good place to start
(make sure that the issue also have the `Accepted`_ label).
That said, these aren't necessarily the easiest tickets.
They are simply things that are explained.
If you still didn't find something to work on, search for the `Sprintable`_ label.
Those tickets are meant to be standalone and can be worked on ad-hoc.

When contributing code, then please follow the standard Contribution
Guidelines set forth at `contribution-guide.org`_.

We have a strict code style that is easy to follow since you just have to
install `pre-commit`_ and it will automatically run different linting tools
(`autoflake`_, `autopep8`_, `docformatter`_, `isort`_, `prospector`_, `unify`_
and `yapf`_) to check your changes before you commit them. `pre-commit` will let
you know if there were any problems that is wasn't able to fix automatically.

To run the `pre-commit` command and check your changes::

    $ pip install -U pre-commit
    $ git add <your-modified-files>
    $ pre-commit run

or to run against a specific file::

    $ pre-commit run --files <file.py>

`pre-commit` can also be run as a git pre-commit hook. You can set this up
with::

    $ pre-commit install

After this installation, the next time you run `git commit` the `pre-commit run`
command will be run immediately and will inform you of the changes and errors.

.. note::

    Our code base is still maturing and the core team doesn't yet recommend
    running this as a pre-commit hook due to the number of changes this will
    cause while constructing a pull request. Independent pull requests with
    linting changes would be a great help to making this possible.


.. _Feature: https://github.com/rtfd/readthedocs.org/issues?direction=desc&labels=Feature&page=1&sort=updated&state=open
.. _Improvement: https://github.com/rtfd/readthedocs.org/issues?q=is%3Aopen+is%3Aissue+label%3AImprovement
.. _Accepted: https://github.com/rtfd/readthedocs.org/issues?q=is%3Aopen+is%3Aissue+label%3AAccepted
.. _Good First Issue: https://github.com/rtfd/readthedocs.org/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22
.. _Sprintable: https://github.com/rtfd/readthedocs.org/issues?q=is%3Aopen+is%3Aissue+label%3ASprintable
.. _contribution-guide.org: http://www.contribution-guide.org/#submitting-bugs

.. _pre-commit: https://github.com/pre-commit/pre-commit
.. _autoflake: https://github.com/myint/autoflake
.. _autopep8: https://github.com/hhatto/autopep8
.. _docformatter: https://github.com/myint/docformatter
.. _isort: https://github.com/timothycrosley/isort
.. _prospector: https://prospector.landscape.io/en/master
.. _unify: https://github.com/myint/unify
.. _yapf: https://github.com/google/yapf

Triaging tickets
----------------

Here is a brief explanation on how we triage incoming tickets to get a better
sense of what needs to be done on what end.

.. note:: You will need Triage permission on the project in order to do this.
          You can ask one of the members of the :doc:`team` to give you access.

Initial triage
~~~~~~~~~~~~~~

When sitting down to do some triaging work, we start with the `list of
untriaged tickets`_. We consider all tickets that do not have a label as
untriaged. The first step is to categorize the ticket into one of the
following categories and either close the ticket or assign an appropriate
label. The reported issue …

… is not valid
    If you think the ticket is invalid comment why you think it is invalid,
    then close the ticket. Tickets might be invalid if they were already fixed
    in the past or it was decided that the proposed feature will not be
    implemented because it does not conform with the overall goal of Read the
    Docs. Also if you happen to know that the problem was already reported,
    reference the other ticket that is already addressing the problem and close the duplicate.

    Examples:

    - *Builds fail when using matplotlib*:
      If the described issue was already fixed, then explain and instruct to
      re-trigger the build.
    - *Provide way to upload arbitrary HTML files*:
      It was already decided that Read the Docs is not a dull hosting platform
      for HTML. So explain this and close the ticket.

.. _triage-not-enough-information:

… does not provide enough information
    Add the label **Needed: more information** if the reported issue does not
    contain enough information to decide if it is valid or not and ask on the
    ticket for the required information to go forward. We will re-triage all
    tickets that have the label **Needed: more information** assigned. If the
    original reporter left new information we can try to re-categorize the
    ticket. If the reporter did not come back to provide more required
    information after a long enough time, we will close the ticket (this will be
    roughly about two weeks).

    Examples:

    - *My builds stopped working. Please help!*
      Ask for a link to the build log and for which project is affected.

… is a valid feature proposal
    If the ticket contains a feature that aligns with the goals
    of Read the Docs, then add the label **Feature**. If the proposal
    seems valid but requires further discussion between core contributors
    because there might be different possibilities on how to implement the
    feature, then also add the label **Needed: design decision**.

    Examples:

    - *Provide better integration with service XYZ*
    - *Achieve world domination* (also needs the label **Needed: design
      decision**)

… is a small change to the source code
    If the ticket is about code cleanup or small changes to existing features
    would likely have the **Improvement** label.
    The distinction for this label is that these issues have a lower priority than a Bug,
    and aren't implementing new features.

    Examples:

    - *Refactor namedtuples to dataclasess*
    - *Change font size for the project's title*

… is a valid problem within the code base:
    If it's a valid bug, then add the label **Bug**. Try to reference related
    issues if you come across any.

    Examples:

    - *Builds fail if conf.py contains non-ascii letters*

… is a currently valid problem with the infrastructure:
    Users might report about web server downtimes or that builds are not
    triggered. If the ticket needs investigation on the servers, then add the
    label **Operations**.

    Examples:

    - *Builds are not starting*

.. _triage-support-tickets:

… is a question and needs answering:
    If the ticket contains a question about the Read the Docs platform or the
    code, then add the label **Support**.

    Examples:

    - *My account was set inactive. Why?*
    - *How to use C modules with Sphinx autodoc?*
    - *Why are my builds failing?*

… requires a one-time action on the server:
    Tasks that require a one time action on the server should be assigned the
    two labels **Support** and **Operations**.

    Examples:

    - *Please change my username*
    - *Please set me as owner of this abandoned project*

After we finished the initial triaging of new tickets, no ticket should be left
without a label.

.. _list of untriaged tickets: https://github.com/rtfd/readthedocs.org/issues?q=is:issue+is:open+no:label

Additional labels for categorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additionally to the labels already involved in the section above, we have a
few more at hand to further categorize issues.

*High Priority*
    If the issue is urgent, assign this label. In the best case also go forward to
    resolve the ticket yourself as soon as possible.

*Good First Issue*
    This label marks tickets that are easy to get started with. The ticket
    should be ideal for beginners to dive into the code base. Better is if the
    fix for the issue only involves touching one part of the code.

*Sprintable*
    Sprintable are all tickets that have the right amount of scope to be
    handled during a sprint. They are very focused and encapsulated.

For a full list of available labels and their meanings, see
:doc:`issue-labels`.

Helpful links for triaging
~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a list of links for contributors that look for work:

- `Untriaged tickets
  <https://github.com/rtfd/readthedocs.org/issues?q=is:issue+is:open+no:label>`_:
  Go and triage them!
- `Tickets labelled with Needed: more information
  <https://github.com/rtfd/readthedocs.org/issues?utf8=✓&q=is:open+is:issue+label:"Needed:+more+information">`_:
  Come back to these tickets once in a while and close those that did not get
  any new information from the reporter. If new information is available, go
  and re-triage the ticket.
- `Tickets labelled with Operations
  <https://github.com/rtfd/readthedocs.org/issues?q=is:open+is:issue+label:Operations>`_:
  These tickets are for contributors who have access to the servers.
- `Tickets labelled with Support
  <https://github.com/rtfd/readthedocs.org/issues?q=is:open+is:issue+label:Support>`_:
  Experienced contributors or community members with a broad knowledge about
  the project should handle those.
- `Tickets labelled with Needed: design decision
  <https://github.com/rtfd/readthedocs.org/issues?q=is:open+is:issue+label:"Needed:+design+decision">`_:
  Project leaders must take actions on these tickets. Otherwise no other
  contributor can go forward on them.

Helping on translations
-----------------------

If you wish to contribute translations, please do so on `Transifex`_.

.. _Transifex: https://www.transifex.com/projects/p/readthedocs/
