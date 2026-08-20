REPO_ROOT = $(shell git rev-parse --show-toplevel)
# Base-only checkout: the builder root and the repo root are the same tree.
A2C_ROOT = $(REPO_ROOT)

SV_COM = $(REPO_ROOT)/common/systemVerilog
# Location of the mixed outptus for lint test
MIXED_DIR = examples/mixed
MIXED_DOT_DB_FILE = $(MIXED_DIR)/.mixed.db
MIXED_DB_FILE = $(MIXED_DIR)/mixed.db

PYSOCKET_DIR = examples/pySocket
PYSOCKET_DOT_DB_FILE = $(PYSOCKET_DIR)/.pySocket.db
PYSOCKET_DB_FILE = $(PYSOCKET_DIR)/pySocket.db

HIER_INCLUDE_DIR = examples/hierInclude
HIER_INCLUDE_DOT_DB_FILE = $(HIER_INCLUDE_DIR)/.hierInclude.db
HIER_INCLUDE_DB_FILE = $(HIER_INCLUDE_DIR)/hierInclude.db

APBDECODE_DIR = examples/apbDecode
APBDECODE_DOT_DB_FILE = $(APBDECODE_DIR)/.apbDecode.db
APBDECODE_DB_FILE = $(APBDECODE_DIR)/apbDecode.db

AXI4SDEMO_DIR = examples/axi4sDemo

HIER_VL_DEMO_DIR = examples/hierVlDemo

IP_TEST_DIR = examples/ip_test
SIMPLE_IP_DIR = examples/simple_ip
XPROJ_PARAM_DIR = examples/xprojParam
XIF_DIR = examples/xif

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

# Artifacts that more than one pipeline target drives. Each is produced here
# once and named as a prerequisite by every target that consumes it, so two
# recursive makes never write the same file concurrently. Without this a reader
# finds a half-written database ("Invalid config item SCHEMA not found",
# KeyError: 'instances'), because the writer creates the .db before filling it
# and the second make then treats the existing file as up to date.
.PHONY : mixed-db nested-db axiDemo-gen
mixed-db:
	make -C $(MIXED_DIR) db

nested-db:
	make -C $(NESTED_DIR) db

# lint-axi and axiDemo drive axiDemo's whole generated output set, not just its
# database, so the shared producer here is gen rather than db.
axiDemo-gen:
	make -C $(AXI_DIR) -j gen

.PHONY : diagram-and-doc
diagram-and-doc : mixed-db nested-db
	mkdir -p examples/tests/out
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
	$(REPO_ROOT)/arch2code.py --db $(NESTED_DIR)/nested.db -r --diagram --depth 7
	cp gv_out/nested.gv $(DIAG_TEST_DIR)/out/nestedDiagramDepth7.gv
	git diff --no-index $(DIAG_TEST_DIR)/golden/nestedDiagramDepth7.gv $(DIAG_TEST_DIR)/out/nestedDiagramDepth7.gv

.PHONY : nested
nested: nested-db
	make -C $(NESTED_DIR)/rundir -j all
	make -C $(NESTED_DIR)/rundir run

.PHONY : axiDemo
# axiDemo migrated to the newer rundir/ build (module-capable). VL_DUT cosim is
# omitted because its producer/consumer RTL are passthrough stubs with no datapath.
axiDemo: axiDemo-gen
	make -C $(AXI_DIR)/rundir -j all
	make -C $(AXI_DIR)/rundir run

.PHONY : axi4sDemo
axi4sDemo:
	make -C $(AXI4SDEMO_DIR)/rundir -j all VL_DUT=1
	make -C $(AXI4SDEMO_DIR)/rundir -j run VL_DUT=1

.PHONY : hierVlDemo
# Hierarchical-layout twin of axi4sDemo: guards the hierarchical verilator wrapper
# build (project-scoped prj/verif dir) and the block-less types-only-context RTL
# package path resolution. Single-node (top node == project root).
hierVlDemo:
	make -C $(HIER_VL_DEMO_DIR)/rundir -j all VL_DUT=1
	make -C $(HIER_VL_DEMO_DIR)/rundir -j run VL_DUT=1

.PHONY : ip-test
ip-test:
	make -C $(IP_TEST_DIR) gen
	make -C $(IP_TEST_DIR)/rundir -j run
	make -C $(IP_TEST_DIR)/rundir -j run-vl
	# Standalone IP projects (ip, ipBridge): model + verilated cosim.
	make -C $(IP_TEST_DIR)/ip/rundir -j run
	make -C $(IP_TEST_DIR)/ip/rundir -j run-vl
	make -C $(IP_TEST_DIR)/bridge/rundir -j run
	make -C $(IP_TEST_DIR)/bridge/rundir -j run-vl

.PHONY : simple-ip
simple-ip:
	make -C $(SIMPLE_IP_DIR) gen
	make -C $(SIMPLE_IP_DIR)/rundir -j run
	make -C $(SIMPLE_IP_DIR)/rundir -j run-vl

.PHONY : xproj-param
# Parameterized interface across separately named project boundaries. Leaf-first:
# each stage project generates its own artifacts before the assembler composes them.
# The cppAxis composition adds the parameterizable-against-parameterizable thunker
# pairs that the de-parameterized boundary cannot produce; the shared composition
# is the straight-through parameterized boundary over one shared parameter identity.
xproj-param:
	make -C $(XPROJ_PARAM_DIR)/gain -j gen
	make -C $(XPROJ_PARAM_DIR)/filter -j gen
	make -C $(XPROJ_PARAM_DIR)/sink -j gen
	make -C $(XPROJ_PARAM_DIR)/uniq -j gen
	make -C $(XPROJ_PARAM_DIR)/uniq/rundir -j run
	make -C $(XPROJ_PARAM_DIR)/cppLeaf -j gen
	make -C $(XPROJ_PARAM_DIR)/cppAxis -j gen
	make -C $(XPROJ_PARAM_DIR)/cppAxis/rundir -j run
	make -C $(XPROJ_PARAM_DIR)/filterShared -j gen
	make -C $(XPROJ_PARAM_DIR)/sinkShared -j gen
	make -C $(XPROJ_PARAM_DIR)/shared -j gen
	make -C $(XPROJ_PARAM_DIR)/shared/rundir -j run

.PHONY : xproj-matrix
# Three-party parameterization matrix: channel + both ports, each parameterized
# or not, over one endpoint IP. The three rows that build and run - literal
# channel, parameterized channel typed by the container's own class template
# parameter, and parameterized channel typed by an unadapted end's Config.
# Every cell drives four samples and checks every field of every sample.
xproj-matrix:
	make -C $(XPROJ_PARAM_DIR)/mtxIp -j gen
	make -C $(XPROJ_PARAM_DIR)/mtxLit -j gen
	make -C $(XPROJ_PARAM_DIR)/mtxLit/rundir -j run
	make -C $(XPROJ_PARAM_DIR)/mtxTpl -j gen
	make -C $(XPROJ_PARAM_DIR)/mtxTpl/rundir -j run
	make -C $(XPROJ_PARAM_DIR)/mtxElect -j gen
	make -C $(XPROJ_PARAM_DIR)/mtxElect/rundir -j run

.PHONY : xproj-reuse
# Cross-project reuse of a params-less TRANSIT container: mtxComp instantiates
# mtxElect's xpMtxElectWrap, which is flagged isParameterizable only because
# parameterizable structures cross its surface. Such a child is not a class
# template, gets no trampoline registrar, and self-registers under its OWNING
# project, so the assembler's createInstance must name that owner. Naming the
# assembler instead compiles clean and aborts at elaboration, which is why this
# is a run target.
# Ordered after xproj-matrix: both recurse into mtxElect/mtxIp, so running them
# concurrently under -j would have two sub-makes generating one tree.
xproj-reuse: xproj-matrix
	make -C $(XPROJ_PARAM_DIR)/mtxComp -j gen
	make -C $(XPROJ_PARAM_DIR)/mtxComp/rundir -j run

.PHONY : xproj-matrix-probes
# The matrix row that does not build, kept out of every aggregate target.
# mtxBare is rejected at make db: nothing can supply the Config its
# parameterized channel is typed with. See examples/xprojParam/README.md.
# The rejection is asserted, not merely tolerated: an mtxBare db build that
# SUCCEEDS means the guard has been lost and fails this target.
xproj-matrix-probes:
	make -C $(XPROJ_PARAM_DIR)/mtxIp -j gen
	# The aborted db build leaves a partial file behind, which would satisfy
	# the db target and make the assertion below vacuous; clean it away first.
	make -C $(XPROJ_PARAM_DIR)/mtxBare clean
	@if make -C $(XPROJ_PARAM_DIR)/mtxBare -j db; then \
	    echo "ERROR: mtxBare db build succeeded; the untypeable-channel rejection no longer fires"; \
	    exit 1; \
	else \
	    echo "OK: mtxBare rejected at db as expected"; \
	fi

.PHONY : xproj-const
# One value, one named constant, every block that has to agree on it. The IP
# owns the knob and its default; the assembler states its use-case value once
# and every variant in that cell - the supporting blocks' and the foreign DUT's
# alike - binds that one constant. Every cell drives four samples through
# generated thunkers and every block asserts the width it resolved.
# Shares no sub-project with any other target, so it needs no ordering.
#
# cstUse is the third cell: a supporting block NAMING the IP's constant in its
# own params: while the assembler binds a NON-default value. Every block in the
# chain resolves the bound width, so the whole chain agrees on one number that
# is stated once. Shares cstIp with the cells above, so it is sequenced after
# them rather than run alongside.
xproj-const:
	make -C $(XPROJ_PARAM_DIR)/cstIp -j gen
	make -C $(XPROJ_PARAM_DIR)/cstBind -j gen
	make -C $(XPROJ_PARAM_DIR)/cstBind/rundir -j run
	make -C $(XPROJ_PARAM_DIR)/cstUse -j gen
	make -C $(XPROJ_PARAM_DIR)/cstUse/rundir -j run

.PHONY : xproj-depth
# containerParam inheritance through two project levels: the customer states one
# algorithm on the wrapper it owns; the mid-level IP declares that parameter but
# states no value for it, sourcing it from its container; and the leaf nested
# inside the mid resolves it. The mid never declares the leaf's DP_ALGO at all.
# Three customer chains resolve to three different algorithms; each checker
# asserts, per sample, that the leaf stamped the algorithm its own Config
# declares, so a broken link fails the run.
# dpMid generates only: its standalone top's driver and sink are empty scaffolds,
# so its own run cannot reach an end of test. dpTop is the buildable top.
# Shares no sub-project with any other target, so it needs no ordering.
#
# dpTop also carries the foreign-Config gate for the testbench External. Its
# testbench container holds xpDpTbPeer instances - PEERS of the DUT, the only
# shape in which the External emits parameterizable instances - at assembler-
# declared variants, so the External must import the owner-qualified Config
# module that declares their structs. Without that import this target fails to
# compile on an undeclared Config struct name.
xproj-depth:
	make -C $(XPROJ_PARAM_DIR)/dpLeaf -j gen
	make -C $(XPROJ_PARAM_DIR)/dpMid -j gen
	make -C $(XPROJ_PARAM_DIR)/dpTop -j gen
	make -C $(XPROJ_PARAM_DIR)/dpTop/rundir -j run

.PHONY : xproj-inherit
# The other parameter-inheritance mechanism: inheritContainerParam types a
# contained instance with the CONTAINER's whole Config rather than sourcing named
# parameters. One container block is instantiated at TWO variants, so the child
# is a different C++ type under each, and each chain's checker asserts per sample
# that the leaves resolved the algorithm its own Config declares.
# Shares no sub-project with any other target, so it needs no ordering.
xproj-inherit:
	make -C $(XPROJ_PARAM_DIR)/inhVar -j gen
	make -C $(XPROJ_PARAM_DIR)/inhVar/rundir -j run

.PHONY : xproj-container-layout
# The layout gate on a container-sourced width, both arms. Both are needed: the
# accepting arm alone would also pass if the gate stopped checking entirely.
#
# cpLayout    - container 16, sibling literal 16, leaf sourced from the
#               container. Equal in truth, so db must ACCEPT.
# cpLayoutBad - container 24, sibling literal 16. Genuinely unequal, so db must
#               REJECT naming 24. That value is reachable only through the
#               container, so it proves the gate resolved per site rather than
#               falling back to the constant's declared default of 8.
# Adjudicated at db and never built. Shares no sub-project, so needs no ordering.
xproj-container-layout:
	make -C $(XPROJ_PARAM_DIR)/cpLayout clean
	make -C $(XPROJ_PARAM_DIR)/cpLayout -j db
	# The aborted db build leaves a partial file behind, which would satisfy
	# the db target and make the assertion below vacuous; clean it away first.
	make -C $(XPROJ_PARAM_DIR)/cpLayoutBad clean
	@if make -C $(XPROJ_PARAM_DIR)/cpLayoutBad -j db > $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log 2>&1; then \
	    echo "ERROR: cpLayoutBad db build succeeded; the layout gate no longer adjudicates a container-sourced width"; \
	    rm -f $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log; \
	    exit 1; \
	elif grep -q '_bitWidth 24' $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log; then \
	    echo "OK: cpLayoutBad rejected at db at the container-resolved width"; \
	    rm -f $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log; \
	else \
	    echo "ERROR: cpLayoutBad was rejected, but not at the container-resolved width 24"; \
	    cat $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log; \
	    rm -f $(XPROJ_PARAM_DIR)/cpLayoutBad/db.log; \
	    exit 1; \
	fi

.PHONY : xproj-variant-unique
# One block's variant declared in two files of ONE project: both declarations
# key on the same (block, variant, project), so one Config survives and the
# other's bindings are lost. db must reject and name both files, since finding
# the pair is the whole difficulty. Adjudicated at db and never built.
#
# The accepting side needs no fixture of its own: ip-test composes ip/variant1
# under two projects, and cpLayout reuses the variant name `use` across three
# blocks of one project. Both are in pipeline-test, so a gate that over-rejected
# either shape would fail there rather than here.
# Shares no sub-project with any other target, so it needs no ordering.
xproj-variant-unique:
	# The aborted db build leaves a partial file behind, which would satisfy
	# the db target and make the assertion below vacuous; clean it away first.
	make -C $(XPROJ_PARAM_DIR)/varUniqBad clean
	@if make -C $(XPROJ_PARAM_DIR)/varUniqBad -j db > $(XPROJ_PARAM_DIR)/varUniqBad/db.log 2>&1; then \
	    echo "ERROR: varUniqBad db build succeeded; the duplicate variant declaration is no longer rejected"; \
	    rm -f $(XPROJ_PARAM_DIR)/varUniqBad/db.log; \
	    exit 1; \
	elif grep -q xpVarUniqBadExtra.yaml $(XPROJ_PARAM_DIR)/varUniqBad/db.log && grep -q xpVarUniqBadTop.yaml $(XPROJ_PARAM_DIR)/varUniqBad/db.log; then \
	    echo "OK: varUniqBad rejected at db naming both declaring files"; \
	    rm -f $(XPROJ_PARAM_DIR)/varUniqBad/db.log; \
	else \
	    echo "ERROR: varUniqBad was rejected, but the diagnostic did not name both declaring files"; \
	    cat $(XPROJ_PARAM_DIR)/varUniqBad/db.log; \
	    rm -f $(XPROJ_PARAM_DIR)/varUniqBad/db.log; \
	    exit 1; \
	fi

.PHONY : xif
# Cross-interface boundary thunker at the testbench/DUT boundary: the edge blocks
# declare a boundary interface differing from the connection interface, so the
# surviving end of each pruned connection is adapted rather than bound. The only
# example where an endpoint's declared interface differs from the connection's,
# which makes it the guard on the adapted-endpoint arm of the bind predicate.
# Model-only; the sink asserts every payload it receives.
#
# xif also carries the container-Config gate for the testbench External. Its
# testbench container declares params:, and one of the two tbPeer instances binds
# a variant that sources every parameter FROM that container - a Config template
# and a maker template both applied to the container's own class template
# parameter, which the External, not being a class template, does not declare.
# The gate lives here rather than in an xprojParam cell because a testbench
# container's own Config struct is only emitted when its config context is owned
# by the same project. Each peer asserts the frame height its partner stamped
# against its own Config, so a broken container-sourced link fails the run.
xif:
	make -C $(XIF_DIR)/rundir -j all
	make -C $(XIF_DIR)/rundir run

.PHONY : xproj-param-probes
# The one recorded cross-project compile failure: three sub-project namespaces
# exporting the same payload identifier. EXPECTED to fail to compile; see
# examples/xprojParam/README.md. Deliberately outside pipeline-test.
xproj-param-probes:
	make -C $(XPROJ_PARAM_DIR)/gain -j gen
	make -C $(XPROJ_PARAM_DIR)/filter -j gen
	make -C $(XPROJ_PARAM_DIR)/sink -j gen
	make -C $(XPROJ_PARAM_DIR)/deparam -j gen
	-make -C $(XPROJ_PARAM_DIR)/deparam/rundir -j all

.PHONY : hello-world
hello-world:
	make -C $(HELLO_DIR)/rundir -j all
	make -C $(HELLO_DIR)/rundir run

.PHONY : apbDecode
# apbDecode migrated to the newer rundir/ build. Full run-vl cosim is omitted
# because blockA's RTL leaves blockATable1 memory uninitialized (a pre-existing
# RTL gap the old lint-only target never exercised).
apbDecode:
	make -C $(APBDECODE_DIR)/rtl lint -j
	make -C $(APBDECODE_DIR)/rundir -j all
	make -C $(APBDECODE_DIR)/rundir run

.PHONY : mixed
mixed: mixed-db
	make -C $(MIXED_DIR)/rundir -j all VL_DUT=1
	make -C $(MIXED_DIR)/rundir run
	make -C $(MIXED_DIR)/rtl lint -j

.PHONY : pySocket
pySocket:
	make -C $(PYSOCKET_DIR)/rundir -j all VL_DUT=1
	make -C $(PYSOCKET_DIR)/rundir run
	make -C $(PYSOCKET_DIR)/rtl lint -j

.PHONY : in-and-out
# sim dropped: inAndOut stays a header-mode SV-generation / moduleSignalBlast
# demo, whose SystemC sim cannot regenerate under this branch's cppm-default
# include. Verilator lint still exercises the generated SV.
in-and-out:
	make -C $(IN_OUT_DIR)/systemVerilog lint -j

.PHONY : lint-hier
lint-hier:
	make -C $(HIER_INCLUDE_DIR)/systemVerilog lint -j

# later add systemc
.PHONY : lint-axi
lint-axi: axiDemo-gen
	make -C $(AXI_DIR)/rtl lint -j

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
	make -C $(NESTED_DIR) db
	$(REPO_ROOT)/arch2code.py --db $(NESTED_DB_FILE) -r --diagram --depth 7 --instance nested_tb --diagramOutFilename uNested --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(HELLO_DIR) db
	$(REPO_ROOT)/arch2code.py --db $(HELLO_DB_FILE) -r --diagram --depth 2 --instance helloWorld_tb --diagramOutFilename uHelloWorld --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(APBDECODE_DIR) db
	$(REPO_ROOT)/arch2code.py --db $(APBDECODE_DB_FILE) -r --diagram --depth 4 --instance top --diagramOutFilename uapbDecode --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	$(REPO_ROOT)/arch2code.py --db $(APBDECODE_DB_FILE) -r --docgen --file $(APBDECODE_DIR)/doc/top_memories.txt --diagramOutDirectory $(DOC_IMAGES_DIR)
	make -C $(IN_OUT_DIR)/arch
	$(REPO_ROOT)/arch2code.py --db $(IN_OUT_DB_FILE) -r --diagram --depth 2 --instance uTop --diagramOutFilename uinAndOut --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
	make -C $(AXI_DIR) db
	$(REPO_ROOT)/arch2code.py -r --db $(AXI_DB_FILE) --diagram --instance u_axiDemo --diagramOutFilename uaxiDemo --diagramOutDirectory $(DOC_IMAGES_DIR) --diagramDeleteGV
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
# Every example project, discovered by the include/make/shared.mk each one owns
# rather than listed here, so a project added later is cleaned without editing
# this rule. Each project's own clean:: reaches the sub-projects it composes.
EXAMPLE_PROJECT_DIRS = $(patsubst %/include/make/shared.mk,%,\
	$(wildcard examples/*/include/make/shared.mk examples/*/*/include/make/shared.mk))

# This should remove all generated files. The db removals and the arch/
# systemVerilog recursions below cover the legacy-layout examples that own no
# project makefile.
clean :
	$(RM) $(MIXED_DOT_DB_FILE) $(MIXED_DB_FILE)
	$(RM) $(APBDECODE_DOT_DB_FILE) $(APBDECODE_DB_FILE)
	$(RM) $(AXI_DOT_DB_FILE) $(AXI_DB_FILE)
	$(RM) $(HIER_INCLUDE_DOT_DB_FILE) $(HIER_INCLUDE_DB_FILE)
	make -C $(IN_OUT_DIR)/arch clean
	make -C $(IN_OUT_DIR)/systemVerilog clean
	make -C common/systemc clean
	for d in $(EXAMPLE_PROJECT_DIRS); do \
		make -C $$d clean || exit $$?; \
	done

.PHONY : unittest
unittest:
	cd unittest && ./run_all_tests.sh

.PHONY : push-test pipeline-test
pipeline-test: diagram-and-doc nested hello-world mixed pySocket in-and-out lint-axi lint-hier apbDecode axiDemo axi4sDemo hierVlDemo ip-test simple-ip xproj-param xproj-matrix xproj-reuse xproj-const xproj-depth xproj-inherit xproj-container-layout xproj-variant-unique xif
push-test: clean unittest pipeline-test

# AI agent rule/skill install targets (agents-setup, cursor-setup, agent-dev-setup, ...).
# Included last so the default goal stays the first target above.
include $(REPO_ROOT)/include/make/a2c-agents.mk
