ARG BASE_IMAGE=arch2code/a2c-dev:2.0
FROM $BASE_IMAGE

ARG USERNAME=
ARG USER_UID=
ARG USER_GID=

RUN apt update && apt install openssh-server vim lcov -y

# Setup defaul bashrc
RUN cat <<EOF >> /etc/skel/.bashrc

# Custom RC additions
if [ -f ~/.bash_custom ]; then
    . ~/.bash_custom
fi
EOF

# New bash custom file default
RUN cat <<EOF > /etc/skel/.bash_custom
export NVM_DIR=/usr/local/nvm
export PATH=\${NVM_DIR}/versions/node/default/bin:\${PATH}

export SYSTEMC_INCLUDE=/usr/include
export SYSTEMC_LIBDIR=/usr/lib
export LD_BOOST=/usr/lib/x86_64-linux-gnu
export BOOST_INCLUDE=/usr/include/boost

export TZ='US/Pacific'
EOF

# Podman hack for escape character substitution in command above
RUN sed -i 's/\\\$/$/g' /etc/skel/.bash_custom

COPY requirements.txt /tmp/a2c-requirements.txt
RUN pip3 install -r /tmp/a2c-requirements.txt

# Create the user
RUN groupadd -f --gid $USER_GID $USERNAME
RUN useradd --uid $USER_UID --gid $USER_GID --create-home $USERNAME --shell /bin/bash

# Enable sudoer access without password request
RUN apt update && apt install sudo -y
RUN usermod -aG sudo $USERNAME
RUN echo $USERNAME:changeme | chpasswd
RUN echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER $USERNAME

CMD sudo service ssh start; bash

