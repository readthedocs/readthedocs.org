My build is using too many resources
====================================

We limit build resources to make sure that users don't overwhelm our build systems.
If you are running into this issue,
there are a couple fixes that you might try:

Reduce formats you're building
------------------------------

You can change the formats of docs that you're building with our YAML file's :ref:`yaml-config:Formats` option.

In particular, the `htmlzip` takes up a decent amount of memory and time,
so disabling that format might solve your problem.

Reduce documentation build dependencies
---------------------------------------

A lot of projects reuse their requirements file for their documentation builds.
If there are extra packages that you don't need for building docs,
you can create a custom requirements file just for documentation.
This should speed up your documentation builds,
as well as reduce your memory footprint.
