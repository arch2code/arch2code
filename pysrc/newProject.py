# New project bootstrap.
#
# This is the only entry point that runs before a project exists, so it cannot
# rely on the normal `make db` / `make newmodule` flow: the makefiles that flow
# needs are themselves scaffolded by newModule. It therefore performs the same
# two steps directly -- create the database from the YAML it just wrote, then
# run newModule -- which breaks the bootstrap cycle without duplicating any of
# the scaffold, layout or merge logic those steps own.
#
# New projects are hierarchical: the project file lives at
# prj/yaml/<name>Project.yaml and the design at yaml/<name>.yaml.

import os
import re
import subprocess

import pysrc.processYaml as processYaml
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.newModule import newModule

# Project names become block names, SystemC class names, SystemVerilog module
# names and C++ namespace fragments, so the accepted set is the intersection of
# what all of them allow.
projectNamePattern = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

projectFileTemplate = \
"""yamlFormat: 2

# Project file for {name}.
#
# Only the settings this project overrides are listed. The directory segments,
# the file map, the templates and the post-parse scripts are all inherited from
# the arch2code base config (and the pro config when pro is present), so there
# is no need to restate them here.

projectName: {name}

# Input files that make up the design. Paths are relative to this file.
projectFiles:
  - ../../yaml/{name}.yaml

# The top level instance of the design
topInstance: {name}_tb

dirs: # only root is supplied; other segments + hierarchicalDirs inherit the base config
  root: ../..    # project root directory relative to this project file

fileGeneration:
  layout: hierarchical
  # Standard copyright statement added to all generated files
  fileCopyrightStatement: "{copyright}"
{fileMap}
instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
    registers:
        alignment: 8
        sortDescending: true
"""

# Firmware is enabled solely by declaring this file map entry; there is no
# schema flag for it. The entry merges by key over the inherited base file map.
firmwareFileMapTemplate = \
"""  # Firmware header generation: one <context>IncludesFW.{{h,cpp}} per yaml
  # context that has firmware-visible content. Headers appear once the design
  # declares registers or regAccess memories.
  fileMap:
    includeFW   : {{ name : "IncludesFW", ext: {{hdr: "h", src: "cpp"}}, cond: {{smartInclude: true}}, mode: context, basePath: fwInc, desc: "yaml based fw include file"}}

"""

designFileTemplate = \
"""# Design description for {name}.
#
# This file is the single source of truth. The model, the RTL, the testbench and
# the firmware headers are all generated from it, so add design intent here and
# regenerate rather than editing generated files.
#
# Sections this file may declare, in dependency order:
#   constants:   architectural parameters, optionally derived with eval:
#   types:       named bit widths built from constants
#   variables:   members of structures
#   structures:  payloads carried over interfaces
#   interfaces:  typed connections, bound to an interfaceType
#   blocks:      the design units
#   instances:   instantiations of blocks into a containment hierarchy
#   connections: which instance drives which, over which interface
#
# See the design-architecture skill for the full schema.

blocks:
  {name}_tb:
    desc: "Testbench container for {name} (root container)"
    hasVl: false
    hasRtl: false
    hasMdl: false
    hasTb: false
  {name}:
    desc: "The {name} device under test"
    hasVl: {hasVl}
    hasRtl: {hasRtl}
    hasMdl: true
    hasTb: true

instances:
  {name}_tb:
    container: {name}_tb # self reference
    instanceType: {name}_tb
    instGroup: top
  u_{name}:  {{ container: {name}_tb, instanceType: {name}, instGroup: top }}
"""

# Generated SOURCE under model/ rtl/ tb/ base/ fw/ verif/ registrar/ is tracked
# deliberately; only build artifacts and the database are ignored.
gitignoreTemplate = \
"""# arch2code build artifacts
**/obj_dir/
**/build/
**/.gen/
**/*.db
**/.*.db
**/*.a
**/*.o
**/*.d
**/*.scgen
**/*.svgen
**/regr/
**/compile_commands.json
**/.clangd
__pycache__
"""


class newProject:

    def __init__(self, args, reader=input):
        # reader is injected so the questionnaire can be driven from a scripted
        # answer sequence in test; interactive use takes the default.
        self._read = reader

        print("Welcome to arch2code new project creation")
        print("This creates a project that builds and runs, in the current directory.")
        print("Nothing decided here is final - every file it writes can be edited later.")
        print("")

        root = self._projectRoot()
        name = self._askProjectName()
        projFile = os.path.join(root, 'prj', 'yaml', f"{name}Project.yaml")
        designFile = os.path.join(root, 'yaml', f"{name}.yaml")
        self._refuseToClobber(projFile, designFile)

        print("")
        print("Firmware support generates a C++ header per yaml context describing the")
        print("registers and memories firmware can reach, and builds firmware sources")
        print("into the model binary.")
        firmware = self._askYesNo("Does this project include firmware?", False)
        print("")
        print("RTL support generates SystemVerilog alongside the SystemC model, and")
        print("enables verilator co-simulation of the design.")
        rtl = self._askYesNo("Does this project include RTL?", True)
        print("")
        print("Copyright statement added to every generated file, for example:")
        print("  Copyright myCompany 2026")
        copyright = self._read().strip()

        self._writeProjectFiles(root, name, projFile, designFile,
                                firmware, rtl, copyright)
        prj = self._createProject(root, name, projFile, args)
        self._reportSetup(prj)
        self._nextSteps(name, firmware, rtl)

    def _projectRoot(self):
        # The scaffolded makefiles set REPO_ROOT from the git top level, so the
        # project must be created there or every REPO_ROOT-relative path in them
        # resolves outside the project.
        try:
            top = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                 capture_output=True, text=True, check=True).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            printError("Not inside a git repository. Run 'git init' first, then re-run "
                       "this command from the repository root.")
            exit(warningAndErrorReport())
        cwd = os.getcwd()
        if os.path.realpath(top) != os.path.realpath(cwd):
            printError(f"Must be run from the repository root ({top}), not {cwd}. "
                       "The generated makefiles resolve every path from the git top level.")
            exit(warningAndErrorReport())
        print(f"Creating project in: {cwd}")
        return cwd

    def _askProjectName(self):
        while True:
            print("What is the name of the project?")
            name = self._read().strip()
            if projectNamePattern.match(name):
                return name
            printError(f"'{name}' is not a usable project name. It becomes a block, "
                       "module and class name, so it must start with a letter and "
                       "contain only letters, digits and underscores.")

    def _askYesNo(self, question, default):
        options = "Y/n" if default else "y/N"
        while True:
            print(f"{question} ({options})")
            answer = self._read().strip().lower()
            if answer == "":
                return default
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False

    def _refuseToClobber(self, *paths):
        # Project creation is not a repair tool. If a project is already here the
        # user wants make newmodule, not a second project written over the first.
        for path in paths:
            if os.path.exists(path):
                printError(f"{path} already exists - this repository already has a "
                           "project. Use 'make newmodule' to add to it.")
                exit(warningAndErrorReport())

    def _writeProjectFiles(self, root, name, projFile, designFile,
                           firmware, rtl, copyright):
        fileMap = firmwareFileMapTemplate.format() if firmware else ""
        self._write(projFile, projectFileTemplate.format(
            name=name, copyright=copyright, fileMap=fileMap))
        self._write(designFile, designFileTemplate.format(
            name=name, hasRtl=str(rtl).lower(), hasVl=str(rtl).lower()))

        gitignore = os.path.join(root, '.gitignore')
        if os.path.exists(gitignore):
            print(f"Keeping existing {gitignore}")
        else:
            self._write(gitignore, gitignoreTemplate)

        if firmware:
            # Generated firmware headers land in fw/; hand-authored firmware
            # sources go in fw/src, which is the dir the scaffolded rundir
            # makefile adds to EXTRA_PRJ_SRC_DIRS.
            os.makedirs(os.path.join(root, 'fw', 'src'), exist_ok=True)

    def _write(self, path, contents):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"Creating {path}")
        with open(path, "w") as f:
            f.write(contents)

    def _createProject(self, root, name, projFile, args):
        # The database name must match a2c-common.mk's
        # A2C_SQLDB_FILE = $(REPO_ROOT)/$(PROJECTNAME).db, so the first make
        # after this sees an up to date database rather than rebuilding it.
        dbFile = os.path.join(root, f"{name}.db")
        print("")
        print("Building project database")
        processYaml.projectCreate(projFile, dbFile)
        # projectCreate chdirs to the project file directory; return to the
        # project root so scaffolding and the closing message are predictable.
        os.chdir(root)
        print("Scaffolding build files and design files")
        prj = processYaml.projectOpen(dbFile)
        newModule(prj, args)
        self._generate(root)
        return prj

    def _generate(self, root):
        # newModule scaffolds files whose generated regions are still empty, and
        # the systemc build does not depend on the generation stamps (only the
        # `gen` target and the verilator wrapper do). A project handed over
        # un-generated therefore fails its first build on unbalanced braces, so
        # fill the regions here through the makefiles just scaffolded. This also
        # proves those makefiles work before the user ever runs them.
        print("")
        print("Generating code")
        result = subprocess.run(['make', 'gen'], cwd=root)
        if result.returncode != 0:
            printError("Generation failed. The project files were written; "
                       "run 'make gen' to see the failure in full.")
            exit(warningAndErrorReport())

    def _reportSetup(self, prj):
        # Report the setup from the merged result rather than re-probing for the
        # pro directory, so this can never disagree with mergeProjectConfig.
        a2cRoot = prj.config.getConfig('A2CROOT')
        setup = "pro" if os.path.exists(os.path.join(a2cRoot, 'pro')) else "base"
        print("")
        print(f"Detected setup: {setup} (arch2code root {a2cRoot})")

    def _nextSteps(self, name, firmware, rtl):
        print("")
        print(f"Project {name} created.")
        print("")
        print("Recommended next step, if you use an AI coding agent:")
        print("  make agents-setup     # installs AGENTS.md, CLAUDE.md and the skill files")
        print("                        # only works now that the project exists")
        print("")
        print("Build and run:")
        print("  make -C rundir run    # build and run the model")
        if rtl:
            print("  make -C rtl lint      # lint the RTL")
        print("")
        print("Then describe your design in yaml/{}.yaml and run 'make newmodule'".format(name))
        print("to scaffold the implementation files for any blocks you add.")
        if firmware:
            print("")
            print("Firmware is enabled. Firmware headers are generated once the design")
            print("declares registers or regAccess memories - see the design-register-decode")
            print("and manage-address-space skills. Put firmware sources in fw/src.")
