FROM readthedocs/build:4.0rc1

ARG username
ARG uid=1000
ARG gid=$uid
ARG label=latest

ENV USERNAME ${username}
ENV UID ${uid}
ENV GID ${gid}

USER root
RUN groupadd --gid $GID $USERNAME
RUN useradd -m --uid $UID --gid $GID $USERNAME
USER $username

CMD ["/bin/bash"]
