A2C_REPO_ROOT = $(shell git rev-parse --show-toplevel)
DOCKERFILE_DIR = $(A2C_REPO_ROOT)/docker

# Default docker vars
DOCKER_IMAGE=a2c-dev
DOCKER_WORKDIR=$(A2C_REPO_ROOT)
DOCKER_CONTAINER=$(USER)_$(DOCKER_IMAGE)

.PHONY: all dockerImage dockerRun

all: dockerImage dockerRun

dockerImage:
	rm -rf $(DOCKERFILE_DIR)/requirements.txt && cp -rp $(A2C_REPO_ROOT)/requirements.txt $(DOCKERFILE_DIR)/requirements.txt
	$(DOCKER_PRE_SH) docker build -t $(USER)/$(DOCKER_IMAGE) $(DOCKERFILE_DIR) --build-arg USERNAME=$(USER) --build-arg USER_UID=$(shell id -u) --build-arg USER_GID=$(shell id -g)
	rm -rf $(DOCKERFILE_DIR)/requirements.txt

dockerRun:
	$(DOCKER_PRE_SH) docker run --rm -ti -v $(DOCKER_WORKDIR):/work --user $(USER) --hostname $(DOCKER_IMAGE) --name $(DOCKER_CONTAINER) --workdir "/work" --entrypoint /bin/bash $(USER)/$(DOCKER_IMAGE)

