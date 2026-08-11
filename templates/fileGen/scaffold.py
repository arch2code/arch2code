# Create-once scaffold templates for a project's user-owned build makefiles.
#
# These four files (top Makefile, include/make/shared.mk, rundir/Makefile,
# rtl/Makefile) carry NO GENERATED_CODE regions: newModule writes each only if
# absent and never rewrites it, and `make gen` never touches them. They are thin
# wrappers around the shared make logic in include/make/a2c-*.mk, emitted in the
# USER-TREE form (REPO_ROOT is the git top level, A2C_ROOT is the builder/
# submodule beneath it). Project identity is parameterized from the project.
# shared.mk always emits the pro a2cPro.mk `-include` line: the leading dash
# makes it conditional at make time (a missing file is silently skipped), so a
# base-only project ignores it and a pro project picks it up with no scaffold
# machinery.
#
# data fields (set by newModule.scaffold_create): target (file key), projectName,
# tbTop, hdlTop.

from pysrc.arch2codeHelper import printError, warningAndErrorReport


def render(args, prj, data):
    match data['target']:
        case 'topMakefile':
            return topMakefile(data)
        case 'sharedMk':
            return sharedMk(data)
        case 'rundirMk':
            return rundirMk(data)
        case 'rtlMk':
            return rtlMk(data)
        case _:
            printError(f"Unknown scaffold target: {data['target']}")
            exit(warningAndErrorReport())


def topMakefile(data):
    return (
        "REPO_ROOT = $(shell git rev-parse --show-toplevel)\n"
        "\n"
        "include $(REPO_ROOT)/include/make/shared.mk\n"
        "\n"
        ".PHONY : clean\n"
        "\n"
        "clean::\n"
        "\trm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)\n"
    )


def sharedMk(data):
    # A2C_PRJ_YAML is emitted only when the project file is not at the
    # a2c-common.mk default (arch/yaml/project.yaml). newModule passes an empty
    # string when the default already resolves, so functional-layout output is
    # unchanged; every hierarchical project needs the explicit line.
    prjYaml = ""
    if data['prjYaml']:
        prjYaml = (
            "\n"
            "# The project file is not at the arch/yaml/project.yaml default that\n"
            "# a2c-common.mk assumes, so point the build at it explicitly.\n"
            f"A2C_PRJ_YAML = $(REPO_ROOT)/{data['prjYaml']}\n"
        )
    return (
        "REPO_ROOT = $(shell git rev-parse --show-toplevel)\n"
        "A2C_ROOT = $(REPO_ROOT)/builder\n"
        "\n"
        "# Project identity. TB_TOP_MODULE is the testbench top passed to the run\n"
        "# binary and HDL_TOP_MODULE is the verilated DUT top; both are best-effort\n"
        "# defaults derived from the design's top block -- verify and edit them to\n"
        "# match your project.\n"
        f"PROJECTNAME = {data['projectName']}\n"
        f"TB_TOP_MODULE = {data['tbTop']}\n"
        f"HDL_TOP_MODULE = {data['hdlTop']}\n"
        f"{prjYaml}"
        "\n"
        "# User-hosted generated-region files: arch2code injects generated sections\n"
        "# into user-authored hosts it does not scaffold (e.g. address defines,\n"
        "# encoder units). List them here, above the a2c-common.mk include, so they\n"
        "# stamp for regeneration and compile with the scaffolded set. Split by host\n"
        "# language; empty by default, uncomment as needed.\n"
        "# EXTRA_SC_GEN_FILES =\n"
        "# EXTRA_SV_GEN_FILES =\n"
        "\n"
        "-include $(A2C_ROOT)/pro/include/make/a2cPro.mk\n"
        "include $(A2C_ROOT)/include/make/a2c-common.mk\n"
    )


def rundirMk(data):
    # A firmware project (one declaring the includeFW fileMap entry) compiles its
    # firmware into the model binary: the hand-authored fw sources, plus the BSP
    # that backs regRead32/regWrite32. The BSP is deliberately not in the default
    # source set, so it is opted into here.
    firmware = ""
    if data['hasFirmware']:
        firmware = (
            "EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)/fw/src\n"
            "EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp\n"
            "\n"
        )
    return (
        "REPO_ROOT = $(shell git rev-parse --show-toplevel)\n"
        "include $(REPO_ROOT)/include/make/shared.mk\n"
        "\n"
        f"{firmware}"
        "EXTRA_CPP_SRC      =\n"
        "EXTRA_CPP_INCLUDES =\n"
        "EXTRA_LD_FLAGS     =\n"
        "\n"
        "# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.\n"
        "EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))\n"
        "\n"
        "include $(A2C_ROOT)/include/make/a2c-systemc.mk\n"
        "\n"
        ".PHONY : run regr\n"
        "\n"
        "run: $(BIN_DIR)/$(BIN)\n"
        "ifndef VL_DUT\n"
        "\t$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)\n"
        "else\n"
        "\t$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)\n"
        "endif\n"
        "\n"
        "regr:\n"
        f"\t$(A2C_ROOT)/regrLauncher.py --build -j8 regr_{data['projectName']}.json $(REGR_USER_OPTS)\n"
    )


def rtlMk(data):
    return (
        "REPO_ROOT = $(shell git rev-parse --show-toplevel)\n"
        "include $(REPO_ROOT)/include/make/shared.mk\n"
        "\n"
        "include $(A2C_ROOT)/include/make/a2c-rtl.mk\n"
    )
