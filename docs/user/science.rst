Documentation in scientific and academic publishing
===================================================

On this page, we explore some of the many tools and practices that *software* documentation and *academic* writing share.
If you are working within the field of science or academia,
this page can be used as an introduction.

.. 2022-08-10
.. Notes about this section:
..
.. This section is intended as a "landing page", meaning that we will allow to
.. mix messages in a pragmatic way UNTIL a permanent location for this landing
.. page is found outside of the RTD User Documentation project.
.. more discussion: https://github.com/readthedocs/readthedocs.org/pull/9460/
..
.. The main ways that the page will be improved are:
.. - Add more focus to documentation perspectives
.. - Move all descriptions of "benefits", i.e. marketing to a separate location
.. - Likely stop using the dropdown element
.. - Continue to function as a "landing" page, but a landing page for
..   documentation resources for scientific/academic projects.

Documentation and technical writing are broad fields.
Their tools and practices have grown relevant to most scientific activities.
This includes building publications, books, educational resources, interactive data science, resources for data journalism and full-scale websites for research projects and courses.

Here's a brief overview of some :doc:`features </reference/features>` that people in science and academic writing love about Read the Docs:

.. dropdown:: 🪄 Easy to use
    :open:

    Documentation code doesn't have to be written by a programmer. In fact, documentation coding languages are designed and developed so you don't have to be a programmer, and there are many writing aids that makes it easy to abstract from code and focus on content.

    Getting started is also made easy:

      * All new to this? Take the official :external+jupyterbook:doc:`Jupyter Book Tutorial <start/your-first-book>`
      * Curious for practical code? See :doc:`/examples`
      * Familiar with Sphinx? See :doc:`/guides/jupyter`

.. dropdown:: 🔋 Batteries included: Graphs, computations, formulas, maps, diagrams and more

    Take full advantage of getting all the richness of :external+jupyter:doc:`Jupyter Notebook <index>` combined with Sphinx and the giant ecosystem of extensions for both of these.

    Here are some examples:

    * Use symbols familiar from math and physics, build advanced proofs. See also: `sphinx-proof <https://sphinx-proof.readthedocs.io/en/latest/syntax.html>`__
    * Present results with plots, graphs, images and let users interact directly with your datasets and algorithms. See also: `Matplotlib <https://matplotlib.org/stable/tutorials/introductory/usage.html>`__, `Interactive Data Visualizations <https://jupyterbook.org/en/stable/interactive/interactive.html>`__
    * Graphs, tables etc. are computed when the latest version of your project is built and published as a stand-alone website. All code examples on your website are validated each time you build.

.. dropdown:: 📚 Bibliographies and external links

    Maintain bibliography databases directly as code and have external links automatically verified.

    Using extensions for Sphinx such as the popular `sphinxcontrib-bibtex <https://sphinxcontrib-bibtex.readthedocs.io/>`__ extension, you can maintain your bibliography with Sphinx directly or refer to entries ``.bib`` files, as well as generating entire Bibliography sections from those files.

.. dropdown:: 📜 Modern themes and classic PDF outputs

    .. figure:: /img/screenshot_rtd_downloads.png
        :align: right

    Use the latest state-of-the-art themes for web and have PDFs and e-book formats automatically generated.

    New themes are improving every day, and when you write documentation based on Jupyter Book and Sphinx, you will separate your contents and semantics from your presentation logic. This way, you can keep up with the latest theme updates or try new themes.

    Another example of the benefits from separating content and presentation logic: Your documentation also transforms into printable books and eBooks.

.. dropdown:: 📐 Widgets, widgets and more widgets

    Design your science project's layout and components with widgets from a rich eco-system of open-source extensions built for many purposes. Special widgets help users display and interact with graphs, maps and more. :external+jupyterbook:doc:`Several <content/components>` `extensions <https://sphinx-gallery.github.io/>`__ are built and invented by the science community.

.. dropdown:: ⚙️ Automatic builds

    Build and publish your project for every change made through Git (GitHub, GitLab, Bitbucket etc). Preview changes via pull requests. Receive notifications when something is wrong. How does this work? Have a look at this video:

    .. video:: https://anti-pattern-sphinx-video-downloader.readthedocs.io/_static/videos/enable-pull-request-builders.mp4
       :width: 100%
       :height: 300

.. dropdown:: 💬 Collaboration and community

    .. figure:: /img/screenshot_edit_on_github.png
        :align: right

    Science and academia have a big kinship with software developers: We ❤️ community. Our solutions and projects become better when we foster inclusivity and active participation. Read the Docs features easy access for readers to suggest changes via your git platform (GitHub, GitLab, Bitbucket etc.). But not just any unqualified feedback. Instead, the *code* and all the tools are available for your community to forge qualified contributions.

    Your readers can become your co-authors!

    Discuss changes via pull request and track all changes in your project's version history.

    Using git does not mean that anyone can go and change your code and your published project. The full ownership and permission handling remains in your hands. Project and organization owners on your git platform govern what is released and who has access to approve and build changes.

.. dropdown:: 🔎 Full search and analytics

    Read the Docs comes with a number of features bundled in that you would have to configure if you were hosting documentation elsewhere.

    Super-fast text search
        Your documentation is automatically indexed and gets its own search function.

    Traffic statistics
        Have full access to your traffic data and have quick access to see which of your pages are most popular.

    Search analytics
        What are people searching for and do they get hits? From each search query in your documentation, we collect a neat little statistic that can help to improve the discoverability and relevance of your documentation.

    SEO - Don't reinvent search engine optimization
        Use built-in SEO best-practices from Sphinx, its themes and Read the Docs hosting. This can give you a good ranking on search engines as a direct outcome of simply writing and publishing your documentation project.

.. dropdown:: 🌱 Grow your own solutions

    The eco-system is open source and makes it accessible for anyone with Python skills to build their own extensions.

We want science communities to use Read the Docs and to be part of the documentation community 💞

Getting started: Jupyter Book
-----------------------------

:external+jupyterbook:doc:`Jupyter Book <intro>` on Read the Docs brings you the rich experience of computed `Jupyter <https://jupyter.org/>`__ documents built together with a modern documentation tool. The results are beautiful and automatically deployed websites, built with Sphinx and :doc:`Executable Book <executablebook:index>` + all the extensions available in this ecosystem.

Here are some popular activities that are well-supported by Jupyter Book:

* Publications and books
* Course and research websites
* Interactive classroom activities
* Data science software documentation


:doc:`Visit the gallery of solutions built with Jupyter Book » <executablebook:gallery>`


Ready to get started?
"""""""""""""""""""""

.. Note that this is a deliberate repetition of a previous segment. Should it repeat? Maybe not, but for now it's nice to be sure that people see it.

* All new to this? Take the official :external+jupyterbook:doc:`Jupyter Book Tutorial » <start/your-first-book>`
* Curious for practical code? See the list of :doc:`example projects » </examples>`
* Familiar with Sphinx? Read :doc:`How to use Jupyter notebooks in Sphinx » </guides/jupyter>`


Examples and users
""""""""""""""""""

.. TODO: get the correct link for
.. :external+jupyter:ref:`the many sub-projects of Jupyter <index.md#sub-project-documentation>`

Read the Docs community for science is already big and keeps growing. The :external+jupyter:doc:`Jupyter Project <index>` itself and `the many sub-projects of Jupyter <https://docs.jupyter.org/en/latest/#sub-project-documentation>`__ are built and published with Read the Docs.

.. grid:: 3
    :gutter: 2
    :padding: 0

    .. grid-item-card:: Jupyter Project Documentation
      :img-top: img/logo_jupyter.png
      :link: https://docs.jupyter.org/

    .. grid-item-card:: Chainladder - Property and Casualty Loss Reserving in Python
      :img-top: img/logo_chain_ladder.png
      :link: https://chainladder-python.readthedocs.io/

    .. grid-item-card:: Feature-engine - A Python library for Feature Engineering and Selection
      :img-top: img/logo_feature_engine.png
      :link: https://feature-engine.readthedocs.io/en/latest/

.. Let's put some logos to sign off


..
    THE FORM IS DISABLED BECAUSE OF FORM SPAM


    How would you use Read the Docs for Science?
    --------------------------------------------

    Would you like to get started with Read the Docs or understand more about the platform? Would you like to help us improve by telling us more about an already existing project?

    Please take 2 minutes to fill in this form.

    .. raw:: html

        <form
          method="POST"
          name="fa-form-1"
          action="https://webhook.frontapp.com/forms/036c4169294f3b04abaa/xP2Ulmxfcgl_mLJrFbGoefmVuqmH7DAfyHD9lt_qbk1heKFev5K8-TEhmpKc8dWdn-rv7bbZMMPjmffxl0mqGRUcrfyOzImtk8zEGJ04E1uuyPE28hqoHExtS20"
          enctype="multipart/form-data"
          accept-charset="utf-8"
        >

    .. list-table::
       :widths: 30 70

       * - Name:
         - |input-name|
       * - Email:
         - |input-email|
       * - What science department are you from, |br| which science field(s) do you work in?
         - |input-deparment-science-field|
       * - Which of these are important to you?
         - |input-interests|
       * - Tell us more about your usecase:
         - |input-usecase|
       * - Should we contact you?
         - |input-contact-me|


    .. raw:: html

        <p>
          <button type="submit" class="btn btn-neutral" style="font-size: 150%">Submit form</button>
        </p>
        </form>


    .. |br| raw:: html

       <br />

    .. |input-email| raw:: html

        <input type="email" name="email">

    .. |input-name| raw:: html

        <input type="text" name="name">

    .. |input-deparment-science-field| raw:: html

        <textarea name="department-science-field" rows="10" style="width: 90%; height: 100px;"></textarea>

    .. |input-interests| raw:: html

        <label for="what1">
          <input id="what1" type="checkbox" name="interests-academic-publishing" value="1">
          Academic publishing (PDFs)
        </label>

        <label for="what2">
          <input id="what2" type="checkbox" name="interests-git-hosting" value="1">
          Maintaining my project with Git
        </label>

        <label for="what3">
          <input id="what3" type="checkbox" name="interests-visualizations" value="1">
          Up-to-date visualizations and computations
        </label>

        <label for="what4">
          <input id="what4" type="checkbox" name="interests-interactive" value="1">
          Interactive visualizations for users
        </label>

        <label for="what5">
          <input id="what5" type="checkbox" name="interests-collaboration" value="1">
          Collaboration and/or getting more community contribution
        </label>

        <label for="what6">
          <input id="what6" type="checkbox" name="interests-hosting-navigation" value="1">
          Publishing and hosting courses and research departments
        </label>

        <label for="what7">
          <input id="what7" type="checkbox" name="interests-search-analytics" value="1">
          Search and analytics
        </label>

        <label for="what8">
          <input id="what8" type="checkbox" name="interests-search-analytics" value="1">
          Previewing new proposals (pull requests)
        </label>

        <input id="body" name="body" type="hidden" value="Science Docs Submission">

    .. |input-contact-me| raw:: html

        <label for="contact">
          <input id="contact" type="checkbox" name="contact-me" value="yes">
          Yes please
        </label>


    .. |input-usecase| raw:: html

        <textarea name="usecase" rows="10" style="width: 90%; height: 100px;"></textarea>
