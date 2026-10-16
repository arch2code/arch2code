ARG BASE_IMAGE=arch2code/a2c-dev:3.0
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

# arch2code environment for login shells; sshd sessions do not inherit the image ENV
RUN cat <<EOF > /etc/profile.d/a2c-env.sh
export XDG_CONFIG_HOME=/usr/local
export NVM_DIR=/usr/local/nvm
case ":\${PATH}:" in
    *":\${NVM_DIR}/versions/node/default/bin:"*) ;;
    *) export PATH=\${NVM_DIR}/versions/node/default/bin:\${PATH} ;;
esac

export SC_BASE=/usr
export SYSTEMC_INCLUDE=/usr/include
export SYSTEMC_LIBDIR=/usr/lib
export BOOST_INCLUDE=/usr/include/boost
export LD_BOOST=/usr/lib/x86_64-linux-gnu

export PIP_BREAK_SYSTEM_PACKAGES=1

export TZ='US/Pacific'
EOF

# Podman hack for escape character substitution in command above
RUN sed -i 's/\\\$/$/g' /etc/profile.d/a2c-env.sh

# Non-login interactive shells (VS Code/Cursor remote terminals) skip profile.d
RUN cat <<EOF >> /etc/bash.bashrc

# arch2code environment
[ -r /etc/profile.d/a2c-env.sh ] && . /etc/profile.d/a2c-env.sh
EOF

# New bash custom file default
RUN cat <<EOF > /etc/skel/.bash_custom
# arch2code defaults live in /etc/profile.d/a2c-env.sh; add personal settings here
EOF

COPY requirements.txt /tmp/a2c-requirements.txt
# Ubuntu 24.04 marks the system Python as externally managed (PEP 668); the env var is ignored by older pip
RUN PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r /tmp/a2c-requirements.txt

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

