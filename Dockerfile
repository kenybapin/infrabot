FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    procps \
    curl \
    docker.io \
    && mkdir /run/sshd

# Copier ta clé publique
COPY authorized_keys /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]