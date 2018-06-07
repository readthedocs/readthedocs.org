if [ $ES_DOWNLOAD_URL ]
then
    wget ${ES_DOWNLOAD_URL}
    tar -xzf elasticsearch-${ES_VERSION}.tar.gz
    ./elasticsearch-${ES_VERSION}/bin/plugin -install elasticsearch/elasticsearch-analysis-icu/2.3.0
    ./elasticsearch-${ES_VERSION}/bin/elasticsearch &
fi
