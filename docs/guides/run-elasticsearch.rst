==========================================
Enabling Elasticsearch on the local server
==========================================

Read the Docs has been using Elasticsearch which is a platform for distributed search and analysis of data in real time. To enable the search feature on your local installation, you need to install the elasticsearch locally and run the Elastic server. 

Installation has been mainly divided into following steps.

1. Installing Java
------------------

Elasticsearch requires JAVA 8 or later. Use .. _Oracle official documentation:http://www.oracle.com/technetwork/java/javase/downloads/index.html or opensource distribution like .. _OpenJDK:http://openjdk.java.net/install/

After installing java, verify the installation by,::

	(READTHEDOCS)$ java -version

The result should be something like this::

	openjdk version "1.8.0_151"
	OpenJDK Runtime Environment (build 1.8.0_151-8u151-b12-0ubuntu0.16.04.2-b12)
	OpenJDK 64-Bit Server VM (build 25.151-b12, mixed mode)


2. Downloading and installing Elasticsearch
-------------------------------------------

Elasticsearch can be downloaded directly from elastic.co in zip, tar.gz, deb, or rpm packages. For Ubuntu, it's best to use the deb (Debian) package which will install everything you need to run Elasticsearch.

RTD currently uses elasticsearch 1.x which can be easily downloaded and installed from the official website (http://elastic.co).

Download it in a directory parallel to where the readthedocs.org project has been stored.::

	(READTHEDOCS)$ wget https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.3.8.tar.gz
	(READTHEDOCS)$ tar -xzf elasticsearch-1.3.8.tar.gz
	(READTHEDOCS)$ cd elasticsearch-1.3.8

Your directory structure after the above command would be:

READTHEDOCS
   |- readthedocs.org
   |- elasticsearch-1.3.8

3. Running Elasticsearch from command line
------------------------------------------

Goto elasticsearch home directory.::

	(READTHEDOCS/elasticsearch-1.3.8)$ cd elasticsearch-1.3.8/bin/
	(READTHEDOCS/elasticsearch-1.3.8/bin)$ ./elasticsearch

To verify run::

	(READTHEDOCS/elasticsearch-1.3.8/bin)$ curl http://localhost:9200

You should get something like:

``{
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
``

4. Index the data available at RTD database
-------------------------------------------

In order to search through the RTD database, you need to index it into the elasticsearch index.:: 

	(READTHEDOCS/readthedocs.org)$ python manage.py reindex_elasticsearch

You are ready to go!
