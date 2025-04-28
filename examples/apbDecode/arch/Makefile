PROJECT_NAME = apbDecode

REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECT_ROOT = $(REPO_ROOT)/examples/$(PROJECT_NAME)

include $(REPO_ROOT)/examples/include/shared.mk

.PHONY: all

all: db

clean: db-clean
