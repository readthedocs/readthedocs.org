if [ $ES_DOWNLOAD_URL ]
then
    wget ${ES_DOWNLOAD_URL}
    tar -xzf elasticsearch-${ES_VERSION}.tar.gz
    ./elasticsearch-${ES_VERSION}/bin/elasticsearch &
fi
