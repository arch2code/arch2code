REPO_ROOT = $(shell git rev-parse --show-toplevel)
A2C_ROOT = $(REPO_ROOT)

# Default docker vars
DOCKER_IMAGE=a2c-dev

help::
	@echo "Usage: make [target] [vars]"
	@echo "Available targets:"

include $(A2C_ROOT)/include/make/a2c-docker.mk
