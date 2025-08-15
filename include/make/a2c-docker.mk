#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef A2C_ROOT
$(error A2C_ROOT is not set - please set to the root of your A2C builder)
endif
ifndef DOCKER_IMAGE
$(error DOCKER_IMAGE is not set - please set to the name of your docker image)
endif

DOCKERFILE_DIR = $(REPO_ROOT)/docker

# Default docker vars
DOCKER_WORKDIR=$(REPO_ROOT)
DOCKER_CONTAINER=$(USER)_$(DOCKER_IMAGE)

DOCKER_BUILD_OPTS=

ifdef DOCKER_BASE_IMAGE
DOCKER_BUILD_OPTS += --build-arg BASE_IMAGE='$(DOCKER_BASE_IMAGE)'
endif

# Allow user to append additional options
DOCKER_BUILD_OPTS += $(DOCKER_USER_BUILD_OPTS)

DOCKER_RUN_OPTS=

# Needed by some RHEL SSH clients with podman (https://bugzilla.redhat.com/show_bug.cgi?id=1923728)
DOCKER_RUN_OPTS += --cap-add=AUDIT_WRITE

ifneq ($(DOCKER_SSH_PORT),'')
DOCKER_RUN_OPTS += -p $(DOCKER_SSH_PORT):22
endif

ifdef DOCKER_RUN_DETACHED
DOCKER_RUN_OPTS += -d
endif

# Allow user to append additional options
DOCKER_RUN_OPTS += $(DOCKER_USER_RUN_OPTS)

.PHONY: all dockerImage dockerRun

all: dockerImage dockerRun

dockerImage:
	if [ -f $(DOCKERFILE_DIR)/Dockerfile.incr ]; then \
	   rm -rf $(DOCKERFILE_DIR)/Dockerfile && cat $(A2C_ROOT)/docker/Dockerfile $(DOCKERFILE_DIR)/Dockerfile.incr > $(DOCKERFILE_DIR)/Dockerfile; \
	fi
	rm -rf $(DOCKERFILE_DIR)/requirements.txt && cp -rpL $(A2C_ROOT)/requirements.txt $(DOCKERFILE_DIR)/requirements.txt
	$(DOCKER_PRE_SH) docker build -t $(USER)/$(DOCKER_IMAGE) $(DOCKERFILE_DIR) --build-arg USERNAME=$(USER) --build-arg USER_UID=$(shell id -u) --build-arg USER_GID=$(shell id -g) $(DOCKER_BUILD_OPTS)
	rm -rf $(DOCKERFILE_DIR)/requirements.txt

dockerRun:
	$(DOCKER_PRE_SH) docker run --rm -ti $(DOCKER_RUN_OPTS) -v $(DOCKER_WORKDIR):/work --user $(USER) --hostname $(DOCKER_IMAGE) --name $(DOCKER_CONTAINER) --workdir '/work' $(USER)/$(DOCKER_IMAGE)

clean::
	if [ -f $(DOCKERFILE_DIR)/Dockerfile.incr ]; then \
		rm -rf $(DOCKERFILE_DIR)/Dockerfile; \
	fi
	rm -rf $(DOCKERFILE_DIR)/requirements.txt

help::
	@echo "  all           - Build the docker image and run the container"
	@echo "  dockerImage   - Build the docker image"
	@echo "  dockerRun     - Run the docker container"
	@echo "Makefile Runtime Variables:"
	@echo "  DOCKER_BASE_IMAGE=<image>           - Base image to build image from"
	@echo "  DOCKER_SSH_PORT=<port>              - SSH port mapping for the container"
	@echo "  DOCKER_RUN_DETACHED=1               - Run the container in detached mode"
	@echo "  DOCKER_PRE_SH=<command>             - Shell command to prepend to docker command (e.g., for setting up environment variables)"
	@echo "  DOCKER_WORKDIR=<path>               - Working directory in the host mounted to /work in container (default: $(REPO_ROOT))"
	@echo "  DOCKER_USER_BUILD_OPTS=<options>    - Additional options to pass to the docker build command"
	@echo "  DOCKER_USER_RUN_OPTS=<options>      - Additional options to pass to the docker run command"
