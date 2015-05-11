Configuration of the production servers
=======================================

This document is to help people who are involved in the production instance of Read the Docs running on readthedocs.org. It contains implementation details and useful hints for the people handling operations of the servers.

Elastic Search Setup
--------------------

You need to install the ICU plugin to make ES work::

        # Use the correct path to the plugin executable that ships with ES.
	/usr/share/elasticsearch/bin/plugin -install elasticsearch/elasticsearch-analysis-icu/2.3.0

::

    from search.indexes import Index, PageIndex, ProjectIndex, SectionIndex
     
    # Create the index.
    index = Index()
    index_name = index.timestamped_index()
    index.create_index(index_name)
    index.update_aliases(index_name)
    # Update mapping
    proj = ProjectIndex()
    proj.put_mapping()
    page = PageIndex()
    page.put_mapping()
    sec = SectionIndex()
    sec.put_mapping()

