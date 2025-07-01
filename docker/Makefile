A2C_REPO_ROOT = $(shell git rev-parse --show-toplevel)
DOCKERFILE_DIR = $(A2C_REPO_ROOT)/docker

# Default docker vars
DOCKER_IMAGE=a2c-dev
DOCKER_WORKDIR=$(A2C_REPO_ROOT)
DOCKER_CONTAINER=$(USER)_$(DOCKER_IMAGE)

DOCKER_RUN_OPTS=

# Needed by some RHEL SSH clients with podman (https://bugzilla.redhat.com/show_bug.cgi?id=1923728)
DOCKER_RUN_OPTS += --cap-add=AUDIT_WRITE

ifneq ($(DOCKER_SSH_PORT),'')
DOCKER_RUN_OPTS += -p $(DOCKER_SSH_PORT):22
endif

ifdef DOCKER_RUN_DETACHED
DOCKER_RUN_OPTS += -d
endif

.PHONY: all dockerImage dockerRun

all: dockerImage dockerRun

dockerImage:
	rm -rf $(DOCKERFILE_DIR)/requirements.txt && cp -rp $(A2C_REPO_ROOT)/requirements.txt $(DOCKERFILE_DIR)/requirements.txt
	$(DOCKER_PRE_SH) docker build -t $(USER)/$(DOCKER_IMAGE) $(DOCKERFILE_DIR) --build-arg USERNAME=$(USER) --build-arg USER_UID=$(shell id -u) --build-arg USER_GID=$(shell id -g)
	rm -rf $(DOCKERFILE_DIR)/requirements.txt

dockerRun:
	$(DOCKER_PRE_SH) docker run --rm -ti $(DOCKER_RUN_OPTS) -v $(DOCKER_WORKDIR):/work --user $(USER) --hostname $(DOCKER_IMAGE) --name $(DOCKER_CONTAINER) --workdir '/work' $(USER)/$(DOCKER_IMAGE)

