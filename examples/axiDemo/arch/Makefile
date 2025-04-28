REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECTNAME = axiDemo
DB_FILE = ../$(PROJECTNAME).db
DOT_DB_FILE = ../.$(PROJECTNAME).db

db: $(DOT_DB_FILE)

YAML_FILES = $(shell find . -type f -name '*.yaml')
PROJ_FILE = $(PROJECTNAME)Project.yaml

all: $(DOT_DB_FILE)
.PHONY: clean

# && touch after the build command only touches the dot file if the previous command is succesful
$(DOT_DB_FILE): $(YAML_FILES)
	$(REPO_ROOT)/arch2code.py --yaml $(PROJ_FILE) --db $(DB_FILE) && touch $(DOT_DB_FILE)

clean:
	$(RM) $(DB_FILE) $(DOT_DB_FILE)
