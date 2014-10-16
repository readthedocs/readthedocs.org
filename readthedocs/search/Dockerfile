

FROM    dockerfile/elasticsearch

RUN     apt-get update && apt-get install -y \
            python-virtualenv \
            python-pip

WORKDIR /search
RUN     virtualenv .venv && \
        .venv/bin/pip install elasticsearch==0.4.3

ADD     elasticsearch.yml /elasticsearch/config/elasticsearch.yml

RUN     /elasticsearch/bin/plugin -install \
            elasticsearch/elasticsearch-analysis-icu/2.3.0 && \
        /elasticsearch/bin/plugin -install mobz/elasticsearch-head


ADD     .   /search

# TODO: sleep could be replaced with more of a polling wait for startup
RUN     /elasticsearch/bin/elasticsearch & \
        sleep 8 && \
        curl -s localhost:9200/_nodes/_all/plugins | python -m json.tool && \
        .venv/bin/python create_index.py
