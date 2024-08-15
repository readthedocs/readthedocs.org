JSDoc
-----

JSDoc 3 is an API documentation generator for JavaScript, similar to Javadoc.
You add documentation comments directly to your source code, right alongside the code itself.
The JSDoc tool will scan your source code and generate HTML documentation.

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.9"
       nodejs: "16"
     jobs:
       post_install:
         # Install dependencies defined in your ``package.json``
         - npm ci
         # Install any other extra dependencies to build the docs
         - npm install -g jsdoc
