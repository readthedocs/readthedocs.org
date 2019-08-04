ARG label

FROM readthedocs/build:${label}

ARG uid
ARG gid

ENV UID ${uid}
ENV GID ${gid}

USER root
RUN groupmod --gid ${GID} docs
RUN usermod --uid ${UID} --gid ${GID} docs
USER docs

CMD ["/bin/bash"]
