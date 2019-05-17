FROM readthedocs/build:latest

ARG username
ARG uid=$uid
ARG gid=$uid

ENV UID ${uid}
ENV GID ${gid}

USER root
RUN groupadd --gid ${GID} docscustom
RUN usermod --uid ${UID} --gid ${GID} docs
USER docs

CMD ["/bin/bash"]
