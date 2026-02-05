Agent skills for Read the Docs
==============================

Trying to figure out how to pass up-to-date information to AI agents is a hard problem.
We have experimented with MCP servers and ``llms.txt``,
but we have found that `Agent Skills <https://agentskills.io/home>`_ are the current best way to handle this problem explicitly.

`Read the Docs Skills <https://github.com/readthedocs/skills>`_ are a collection of Agent Skills that help AI agents work with Read the Docs APIs and configuration.
They are designed to keep agent output aligned with our documented behavior and reduce manual verification.
This page highlights two foundational skills that cover the most common workflows: the Read the Docs API skill and the Read the Docs Config Writer skill.

What is a skill?
----------------

A skill is a small, self-contained package with a ``SKILL.md`` that teaches an agent how to perform a specific task.
Skills are automatically discovered by compatible agents.
When a request matches a skill description, the agent loads the relevant ``SKILL.md`` and follows its steps.
To learn more about Agent Skills, see the `Agent Skills home page <https://agentskills.io/home>`_.

Featured skills
---------------

`Read the Docs API <https://github.com/readthedocs/skills/blob/main/skills/readthedocs-api/SKILL.md>`_
  The Read the Docs API skill gives your AI agent the ability to interact with the Read the Docs REST API.
  If you want to manage updates to your project (eg. adding a redirect for the current PR), this skill will help you do that.

`Read the Docs Config Writer <https://github.com/readthedocs/skills/blob/main/skills/readthedocs-write-config/SKILL.md>`_
  Create or update ``.readthedocs.yaml`` configuration files.
  Use it to adjust build images, tools, dependency installs, or build jobs.

Install and use
---------------

Clone the repository and use the skill directories directly:

.. code-block:: bash

   git clone https://github.com/readthedocs/skills.git

If your agent supports the `Agent Skills CLI <https://whatisskills.com/cli-docs>`_, you can install the repository with:

.. code-block:: bash

   npx skills add readthedocs/skills

Point your agent at the ``skills/`` directory and ask a question that matches a skill description.

Available skills
----------------

See the `Read the Docs Skills repository <https://github.com/readthedocs/skills>`_ for the latest list of skills and details.

.. seealso::

   :doc:`/config-file/index`
     Learn about the ``.readthedocs.yaml`` configuration file.

   :doc:`/api/index`
     Read the Read the Docs API documentation.
