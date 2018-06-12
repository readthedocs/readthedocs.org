==========================================
Enabling Elasticsearch on the local server
==========================================

Read the Docs has been using Elasticsearch for indexing and searching. To enable this on your local installation, you need to install elasticsearch and run the Elastic server locally. 

Installation has been mainly divided into following steps.

Installing Java
---------------

Elasticsearch requires Java 8 or later. Use `Oracle official documentation <http://www.oracle.com/technetwork/java/javase/downloads/index.html>`_. 
or opensource distribution like `OpenJDK <http://openjdk.java.net/install/>`_.

After installing java, verify the installation by,::

    $ java -version

The result should be something like this::

    openjdk version "1.8.0_151"
    OpenJDK Runtime Environment (build 1.8.0_151-8u151-b12-0ubuntu0.16.04.2-b12)
    OpenJDK 64-Bit Server VM (build 25.151-b12, mixed mode)


Downloading and installing Elasticsearch
----------------------------------------

Elasticsearch can be downloaded directly from elastic.co. For Ubuntu, it's best to use the deb (Debian) package which will install everything you need to run Elasticsearch.

RTD currently uses elasticsearch 1.x which can be easily downloaded and installed from `elastic.co 
<https://www.elastic.co/downloads/past-releases/elasticsearch-1-3-8/>`_.

Install the downloaded package by following command::

    $ sudo apt install .{path-to-downloaded-file}/elasticsearch-1.3.8.deb

Custom setup
------------

You need the icu plugin::

    $ elasticsearch/bin/plugin -install elasticsearch/elasticsearch-analysis-icu/2.3.0

Running Elasticsearch from command line
---------------------------------------

Elasticsearch is not started automatically after installation. How to start and stop Elasticsearch depends on whether your system uses SysV init or systemd (used by newer distributions). You can tell which is being used by running this command::

    $ ps -p 1   

**Running Elasticsearch with SysV init**

Use the ``update-rc.d command`` to configure Elasticsearch to start automatically when the system boots up::

    $ sudo update-rc.d elasticsearch defaults 95 10

Elasticsearch can be started and stopped using the service command::

    $ sudo -i service elasticsearch start
    $ sudo -i service elasticsearch stop

If Elasticsearch fails to start for any reason, it will print the reason for failure to STDOUT. Log files can be found in /var/log/elasticsearch/.

**Running Elasticsearch with systemd**

To configure Elasticsearch to start automatically when the system boots up, run the following commands::

    $ sudo /bin/systemctl daemon-reload
    $ sudo /bin/systemctl enable elasticsearch.service

Elasticsearch can be started and stopped as follows::

    $ sudo systemctl start elasticsearch.service
    $ sudo systemctl stop elasticsearch.service

To verify run::

    $ curl http://localhost:9200


You should get something like::

    {
        status: 200,
        name: "Amina Synge",
        version: {
            number: "1.3.8",
            build_hash: "475733ee0837fba18c00c3ee76cd49a08755550c",
            build_timestamp: "2015-02-11T14:45:42Z",
            build_snapshot: false,
            lucene_version: "4.9"
        },
        tagline: "You Know, for Search"
    }

Index the data available at RTD database
----------------------------------------

You need to create the indexes::

    $ python manage.py provision_elasticsearch

In order to search through the RTD database, you need to index it into the elasticsearch index:: 

    $ python manage.py reindex_elasticsearch

You are ready to go!
