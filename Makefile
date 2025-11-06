REPO_ROOT = $(shell git rev-parse --show-toplevel)

SV_COM = $(REPO_ROOT)/common/systemVerilog
# Location of the mixed outptus for lint test
MIXED_DIR = examples/mixed
MIXED_DOT_DB_FILE = $(MIXED_DIR)/.mixed.db
MIXED_DB_FILE = $(MIXED_DIR)/mixed.db

HIER_INCLUDE_DIR = examples/hierInclude
HIER_INCLUDE_DOT_DB_FILE = $(HIER_INCLUDE_DIR)/.hierInclude.db
HIER_INCLUDE_DB_FILE = $(HIER_INCLUDE_DIR)/hierInclude.db

APBDECODE_DIR = examples/apbDecode
APBDECODE_DOT_DB_FILE = $(APBDECODE_DIR)/.apbDecode.db
APBDECODE_DB_FILE = $(APBDECODE_DIR)/apbDecode.db

AXI4SDEMO_DIR = examples/axi4sDemo

IN_OUT_DIR = examples/inAndOut
IN_OUT_DOT_DB_FILE = $(IN_OUT_DIR)/.inAndOut.db
IN_OUT_DB_FILE = $(IN_OUT_DIR)/inAndOut.db

NESTED_DIR = examples/nested
NESTED_DB_FILE = $(NESTED_DIR)/nested.db

HELLO_DIR = examples/helloWorld
HELLO_DB_FILE = $(HELLO_DIR)/helloWorld.db

DOC_IMAGES_DIR = $(REPO_ROOT)/document/source/modules/ROOT/images
DOC_PAGES_DIR = $(REPO_ROOT)/document/source/modules/ROOT/pages
DOC_EXAMPLES_DIR = $(REPO_ROOT)/document/source/modules/ROOT/examples

DIAG_TEST_DIR = examples/tests

AXI_DIR = examples/axiDemo
AXI_DOT_DB_FILE = $(AXI_DIR)/.axiDemo.db
AXI_DB_FILE = $(AXI_DIR)/axiDemo.db

JIRA_TABLE = $(DOC_PAGES_DIR)/jiraItems.adoc


.PHONY : systemc
systemc: nested hello-world axiDemo

.PHONY : diagram-and-doc
diagram-and-doc :
	mkdir -p examples/tests/out
	make -C $(MIXED_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --docgen --depth 1 > $(DIAG_TEST_DIR)/out/mixedDocDepth1.txt
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --docgen --depth 2 > $(DIAG_TEST_DIR)/out/mixedDocDepth2.txt
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --docgen --depth 3 > $(DIAG_TEST_DIR)/out/mixedDocDepth3.txt
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 1
	cp gv_out/mixed.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth1.gv
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 2
	cp gv_out/mixed.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth2.gv
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 3
	cp gv_out/mixed.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth3.gv
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDocDepth1.txt $(DIAG_TEST_DIR)/out/mixedDocDepth1.txt
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDocDepth2.txt $(DIAG_TEST_DIR)/out/mixedDocDepth2.txt
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDocDepth3.txt $(DIAG_TEST_DIR)/out/mixedDocDepth3.txt
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDiagramDepth1.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth1.gv
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDiagramDepth2.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth2.gv
	git diff --no-index $(DIAG_TEST_DIR)/golden/mixedDiagramDepth3.gv $(DIAG_TEST_DIR)/out/mixedDiagramDepth3.gv
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --drawStructure nestedSt/mixed.yaml --diagramOutFilename nestedSt --diagramOutDirectory $(DIAG_TEST_DIR)/out --diagramDeleteGV
	git diff --no-index $(DIAG_TEST_DIR)/out/nestedSt.svg $(DIAG_TEST_DIR)/golden/nestedSt.svg
	make -C $(NESTED_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(NESTED_DIR)/nested.db -r --diagram --depth 6
	cp gv_out/nested.gv $(DIAG_TEST_DIR)/out/nestedDiagramDepth6.gv
	git diff --no-index $(DIAG_TEST_DIR)/golden/nestedDiagramDepth6.gv $(DIAG_TEST_DIR)/out/nestedDiagramDepth6.gv

.PHONY : nested
nested:
	make -C $(NESTED_DIR)/model run -j

.PHONY : axiDemo
axiDemo:
	make -C $(AXI_DIR) all -j
	make -C $(AXI_DIR) run -j

.PHONY : axi4sDemo
axi4sDemo:
	make -C $(AXI4SDEMO_DIR)/rundir -j all VL_DUT=1
	make -C $(AXI4SDEMO_DIR)/rundir -j run VL_DUT=1

.PHONY : hello-world
hello-world:
	make -C $(HELLO_DIR)/model run -j

.PHONY : apbDecode
apbDecode:
	make -C $(APBDECODE_DIR)/systemVerilog lint -j
	make -C $(APBDECODE_DIR) all -j
	make -C $(APBDECODE_DIR) run -j

.PHONY : mixed
mixed:
	make -C $(MIXED_DIR)/systemVerilog lint -j
	make -C $(MIXED_DIR) all -j
	make -C $(MIXED_DIR) run -j

.PHONY : in-and-out
in-and-out:
	make -C $(IN_OUT_DIR)/systemVerilog lint -j
	make -C $(IN_OUT_DIR)/systemVerilog sim -j

.PHONY : lint-hier
lint-hier:
	make -C $(HIER_INCLUDE_DIR)/systemVerilog lint -j

# later add systemc
.PHONY : lint-axi
lint-axi:
	make -C $(AXI_DIR)/systemVerilog lint -j

.PHONY : doc-build
# last line; antora must be run at repo root so bypassing the aboslute path(s)
doc-build :
	make -C $(MIXED_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 1 --instance uTop --diagramOutFilename uTopDepth1 --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 2 --instance uTop --diagramOutFilename uTopDepth2 --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --diagram --depth 3 --instance uTop --diagramOutFilename uTopDepth3 --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --drawStructure nestedSt/mixed.yaml --diagramOutFilename nestedSt --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --drawStructure aSt/mixed.yaml --diagramOutFilename aSt --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --drawStructure nestedSt/mixed.yaml --diagramOutFilename nestedStWhite --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV --colors white
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --docgen --file $(DOC_PAGES_DIR)/mixedMemories.adoc --diagramOutDirectory $(DOC_IMAGES_DIR)
	$(REPO_ROOT)/arch2code.py --db $(MIXED_DB_FILE) -r --docgen --file $(DOC_PAGES_DIR)/mixedBlockBadoc.adoc --diagramOutDirectory $(DOC_IMAGES_DIR)
	make -C $(NESTED_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(NESTED_DB_FILE) -r --diagram --depth 6 --instance uTop --diagramOutFilename uNested --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(HELLO_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(HELLO_DB_FILE) -r --diagram --depth 2 --instance uTop --diagramOutFilename uHelloWorld --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(APBDECODE_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(APBDECODE_DB_FILE) -r --diagram --depth 4 --instance uTop --diagramOutFilename uapbDecode --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(APBDECODE_DB_FILE) -r --docgen --file $(APBDECODE_DIR)/doc/top_memories.txt --diagramOutDirectory $(DOC_IMAGES_DIR)
	make -C $(IN_OUT_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(IN_OUT_DB_FILE) -r --diagram --depth 2 --instance uTop --diagramOutFilename uinAndOut --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(AXI_DIR)/arch
	$(REPO_ROOT)/arch2code.py -r --db $(AXI_DB_FILE) --diagram --instance uTop --diagramOutFilename uaxiDemo --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(HIER_INCLUDE_DIR)/arch
	$(REPO_ROOT)/arch2code.py -r --db $(HIER_INCLUDE_DB_FILE) --diagram --depth 3 --instance uTop --diagramOutFilename uTopHierInclude --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	antora --log-failure-level=error antora-playbook.yml

.PHONY : doc-hash
doc-hash :
	$(REPO_ROOT)/getJiras.py > $(JIRA_TABLE)
	@echo ":builddate: blah" > $(DOC_PAGES_DIR)/DateAndHash.adoc && echo ":revhash: blah" >> $(DOC_PAGES_DIR)/DateAndHash.adoc && echo ":revnumber: blah" >> $(DOC_PAGES_DIR)/DateAndHash.adoc
	$(eval DATE := $(shell TZ=PST+8 date))
	$(eval HASH := $(shell git log HEAD -1 --pretty='format:%C(auto)%h %ad'))
	$(eval REV := $(shell $(REPO_ROOT)/arch2code.py --version --readonly))
	@sed 's/^\:builddate\:.*/\:builddate\: $(DATE)/' $(DOC_PAGES_DIR)/DateAndHash.adoc > tmp
	@sed 's/^\:revhash\:.*/\:revhash\: $(HASH)/' tmp > $(DOC_PAGES_DIR)/DateAndHash.adoc
	@sed 's/^\:revnumber\:.*/\:revnumber\: $(REV)/' $(DOC_PAGES_DIR)/DateAndHash.adoc > tmp && mv tmp $(DOC_PAGES_DIR)/DateAndHash.adoc

.PHONY : clean
# This should remove all generated files.
clean :
	$(RM) $(MIXED_DOT_DB_FILE) $(MIXED_DB_FILE)
	$(RM) $(APBDECODE_DOT_DB_FILE) $(APBDECODE_DB_FILE)
	$(RM) $(AXI_DOT_DB_FILE) $(AXI_DB_FILE)
	$(RM) $(HIER_INCLUDE_DOT_DB_FILE) $(HIER_INCLUDE_DB_FILE)
	make -C $(IN_OUT_DIR)/arch clean
	make -C $(IN_OUT_DIR)/systemVerilog clean
	make -C common/systemc clean
	make -C $(MIXED_DIR) clean
	make -C $(NESTED_DIR)/model clean
	make -C $(HELLO_DIR)/model clean
	make -C $(APBDECODE_DIR) clean
	make -C $(AXI_DIR) clean
	make -C $(AXI4SDEMO_DIR) clean

.PHONY : push-test pipeline-test
pipeline-test: diagram-and-doc nested hello-world mixed in-and-out lint-axi lint-hier apbDecode axiDemo axi4sDemo
push-test: clean pipeline-test
