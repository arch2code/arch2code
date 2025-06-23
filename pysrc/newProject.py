# file generation
# this file contains the templates neceesary to generate blank files for a new module
from pysrc.arch2codeHelper import printError, warningAndErrorReport
import os
import re
from jinja2 import Template

def clean_directory_name(name):
    # Remove leading and trailing whitespace.
    cleaned = name.strip()
    # Replace one or more whitespace characters in the middle with an underscore.
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Remove any characters that are not allowed in directory names.
    # Here we remove < > : " / \ | ? * (adjust this list as needed)
    cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
    return cleaned

functionalDirectories = {"yaml": "arch/yaml", "model": "model", "rtl": "rtl", "verif": "verif", "tb": "tb", "base": "base"}

projectTemplate = \
"""
# Example project file that defines project level information

projectName: {{data.projectName}}

# project files can be regular input files, regular input files with additional projectFiles sections, or additional ProjectFiles.
# note in the case of additional project files any top level controls (such as schema:) are ignored
# relative path names are resolved based on location of project file (this includes sub projects)
projectFiles:
  - testbench/topTestbench.yaml

# uncomment to use a custom schema file, otherwise the default schema is used
#dbSchema: config/schema.yaml

addressControl: {{data.addressControlFile}}

topInstance: testbench

# uncomment to use custom templates, otherwise the default templates are used
#docConfig : config/docConfig.yaml
#cppConfig : config/cppConfig.yaml
#svConfig : config/svConfig.yaml

# this is a list of locations, orthogonal to design hierarchy, that maps out the functional layout of the project
# $xxx is a macro that is replaced by the directory. Note macro replacement only works as first character 
# root defines the top level directory for the project, and other directories are defined relative to this.
# note that $a2c is automatically created by the system and points to the a2c directory
dirs: 
  root: ../..    # project root directory relative to project file - required
  base: $root/base             # for block base classes
  model: $root/model           # systemC model implementation
  rtl: $root/rtl               # RTL implementation
  vl_wrap: $root/verif/vl_wrap # rtl wrapper files
  tb: $root/tb                 # testbench definition files 

# information about project directory structure to enable simplified maintenance
# and generation of file for new blocks. Note that directory structure will mirror
# architecture hierarchy.
fileGeneration:
  template: $a2c/templates/fileGen/fileGen.py
  fileMap:
    # generation has 2 modes, block and context
    # block creates a file per design block and cond: depend on the block definition
    # context creates a file per yaml file and cond: depend on the yaml file (typically this is for includes/packages)
    # name will be added to the module name to generate a filename plus associated extensions
    # path to the file is based on dirs section and otherwise follows block/yaml file structure
    # this means if blocks are defined in a file called cpu/cpu.yaml ie in the cpu directory then the implementation file is in cpu unless overridden in the block definition
    # if blockDirs is true then the file is placed in a directory the block appended as well
    # note that basePath should reference a path key in the dirs section
    # cond: matches fields in the block definition, if all fields are true then the file is generated
    # smartInclude is yaml based instead of block based and is used to generate include files based on the yaml file 
    # if smartInclude is true then files are only created if there is content to include. If smartInclude: false then the file is always created
    blockBase   : { name : "Base",            ext: {hdr: "h"},             cond: {hasMdl: true},                mode: block,   basePath: base,    desc: "Module Base class header file"}
    block       : { name : "",                ext: {hdr: "h", src: "cpp"}, cond: {hasMdl: true},                mode: block,   basePath: model,   desc: "Model implementation file"}
    rtlModule   : { name : "",                ext: {sv: "sv"},             cond: {hasRtl: true},                mode: block,   basePath: rtl,     desc: "RTL implementation file"}
    vlSvWrap    : { name : "_hdl_sv_wrapper", ext: {sv: "sv"},             cond: {hasVl: true, hasRtl: true},   mode: block,   basePath: vl_wrap, variant: true, desc: "SystemVerilog HDL module wrapper for verilator"}
    vlScWrap    : { name : "_hdl_sc_wrapper", ext: {hdr: "h"},             cond: {hasVl: true, hasRtl: true},   mode: block,   basePath: vl_wrap, desc: "SystemC Verilated HDL module derived class header file"}
    # tandem      : { name : "Tandem",          ext: {hdr: "h", src: "cpp"}, cond: {hasMdl: true, hasRtl: true},  mode: block,   basePath: base,    desc: "Model tandem module wrapper class header file"}
    testbench   : { name : "Testbench",       ext: {hdr: "h", src: "cpp"}, cond: {hasTb: true}, blockDir: true, mode: block,   basePath: tb,      desc: "Testbench implementation file"}
    tbConfig    : { name : "Config",          ext: {src: "cpp"},           cond: {hasTb: true}, blockDir: true, mode: block,   basePath: tb,      desc: "Testbench config files"}
    tbExternal  : { name : "External",        ext: {hdr: "h", src: "cpp"}, cond: {hasTb: true}, blockDir: true, mode: block,   basePath: tb,      desc: "Testbench external files"}
    include     : { name : "Includes",        ext: {hdr: "h", src: "cpp"}, cond: {smartInclude: true},          mode: context, basePath: model,   desc: "yaml based include file"}
    includeFW   : { name : "IncludesFW",      ext: {hdr: "h", src: "cpp"}, cond: {smartInclude: true},          mode: context, basePath: fwInc,   desc: "yaml based fw include file"}
    package     : { name : "_package",        ext: {sv: "sv"},             cond: {smartInclude: true},          mode: context, basePath: rtl,     desc: "yaml based package file"}
  # standard copyright statement to be added to all generated files - change to suite your company
  fileCopyrightStatement: "{{data.copywrite}}"
postProcess:
  - ../../builder/base/examples/common/postParseRegister.py
  - ../../builder/base/examples/common/postParseChecks.py

"""


class newProject:
    name = ""
    projDir = ""
    blocks = list()
    cwd = os.getcwd()
    def __init__(self, args):
        print("Welcome to arch2code new project creation")
        print("This program will step you through the process of creating a new project with arch2code")
        print("The program will create directories base on current directory so its recommended to run")
        print("this in the root of your project / git repository")
        print("Current directory is: " + self.cwd)
        print("You are free to modify the project after creation or go your own path as no decision made here is final")
        print("this program just creates a simple set of yaml and directories to get you started")
        print("Please answer the following questions:")
        print("What is the name of the project?")
        self.name = input()
        self.projDir = clean_directory_name(self.name)
        print("A project consists of a set of yaml file describing the hierarchy of the project")
        print("and source files in SystemC, SystemVerilog to build model, RTL and testbenchs")
        print("the different target implementations share identical directory structures")
        print("to take advantage of the newModule function when you add blocks to a design.")
        print("Note that this is not strictly required as it is ultimately up to you how you organise your project")
        print("Project directory structure (showing subset of directories)")
        print("ip1/arch/yaml  <- here it is assuming that you have some ip that is shared between projects (possibly as a git submodule)")
        print("   /model")
        print("   /rtl")
        print("   /verif")
        print("   /tb")       
        print("arch/yaml/block1")
        print("         /block2")
        print("model/block1")       
        print("     /block2")
        print("verif/block1")
        print("     /block2")       
        print("rtl/block1")
        print("   /block2")
        print("tb/block1")       
        print("  /block2")
        print("Specify where arch2code project file is stored")
        print("this directory contains the basic project information and is the input to the tool")
        config = "arch/yaml"
        print(f"(enter for default: {config})")
        configDir = input()
        if configDir == "":
            configDir = config
            functionalDirectories["yaml"] = configDir
        print("Provide a top level container block for the project, default is top")
        topBlock = input()
        if topBlock == "":
            topBlock = "top"
        print("Do you want a small demo hello world project created? or would you like to specify a few blocks (demo = y, specify = n)")
        while True:
            demo = input()
            if demo == "y":
                break
            if demo == "n":
                break
        if demo == "y":
            self.createDemoProject(configDir, topBlock)
        else:
            self.createUserProject(configDir, topBlock)
        self.createDirs()
        self.generateProjFile()

    def createDirs(self):
        print("Creating directories")
        for dirType, dirName in functionalDirectories.items():
            for block in self.blocks:
                os.makedirs(f"{dirName}/{block}", exist_ok=True)

    def generateProjFile(self):
        print("Enter your default copywrite notice, this can be updated later in the project file")
        print("for example: Copyright myCompany 2025")
        copywrite = input()

        tm = Template(projectTemplate, trim_blocks=True, lstrip_blocks=True)
        data = {"projectName": self.name, "addressControlFile": "config/addressControl.yaml", "copywrite": copywrite}
        projectFileContents = tm.render(data=data)
        print("Creating directories")
        with open (f"{functionalDirectories['yaml']}/project.yaml", "w") as f:
            f.write(projectFileContents)

    def createDemoProject(self, configDir, topBlock):
        pass

    def createUserProject(self, configDir, topBlock):
        print("Provide a list of container blocks for the project (at least 2), you can add/delete more later manually")
        print("A container block is a block that contains other blocks and is grouped at the design level")
        print("an example list might be: top, cpu, memory, peripheral. Or in the example above block1, block2")
        print("Press enter to finish")
        while True:
            block = input()
            if block == "":
                break
            self.blocks.append(block)


topTestBenchTemplate = \
"""
# this file contains the top level definitions and connections for project
include:


# constants / parameters are architectural level variables that can be used to control the size of structures,
# variables, number of instances, etc.
## constantname: is the constant's name and key for usage by any other dictionary doing a lookup, required
## for any other key in any other dictionary
### value: followed by a number to indicate the value for this constant, required if eval is not used
### desc: followed by a string is a description of this constant, required
### eval: optional in place of value, this is a math function that can be used to make a constant from other constant
###       supports +, -, *, and / math.
### to reference another constant use $CONSTNAME
#constants:

#types:

# variables used as members of structures, only structures are attached to interfaces
## variablename: is the variable's name and key for usage by any other dictionary doing a lookup, required
### width: followed by a number or a constant's key (constantname), required
### desc: followed by a string is a description of this variable, required
#variables:

# structures are collections of variables, or other structures, structures are the main communication tool from block to block on any interface
## structureName: is the structure's name and key for usage by any other dictionary doing a lookup, required
### - variablename
### - strcuturename
### dash (-) followed by a variablename or a structureName, the dash is making a list of variables or structures at least one is required to create a valid structure
#structures:

# interfaces are needed to make any connection from one instance of a block to another block's instance
## interfacename: is the interface's name and key for usage by any other dictionary doing a lookup, required
### interfaceType: followed by a string that links to a valid interface type
####        i.e. rdy_vld could be defined as a ready valid interface
####             static could be defined as a single port interface with a structure and no protocol
####             req_ack could be defined as a request acknowledge interface with a structure in both directions
### structures: is a list of dictionaries, each dictionary has two keys, each item in the list is one per structure on this interface
###                 some interfaces can have more than one structure but all interfaces must have at least one
#### dash (-) followed by a dictionary
#### structureName: followed by a string is a key reference to the structures dictionary
#### structureType: followed by a string, the structureType is what the structureName gets bound to during generation
####                    a System Verilog interface may have more than one structureType defined and that is what each
####                    structureName gets bound to during generation, similar for System C
### desc: followed by a string is a description of this interface, required
#interfaces:

# blocks these are subsystems or blocks that can be instanced one or more times
## blockname: followed by a name that gives this object (block) a unique key
### desc: followed by a string is a description of this block, required
### blockGroup: followed by a string that is a key to the group this block belongs to, required
blocks:
  testbench:
    desc: Top testbench
    blockGroup: blockTop
    hasVl: false
    hasRtl: false
    hasMdl: false

# instances, these are instantiations of objects
#   implies a top level of some kind that is instancing objects, an instance can instance other objects, optional nesting
## instancename: is the instance name being instanced, required
### instanceType: followed by a string which is the key to finding which object is being instanced (objectname), required
### in the top level testbench the main ip (top) is instanced, along with whatever models are necessary to support the testbench
instances:
  u_top:          { container: testbench,  instanceType: top,           instGroup: allInstances,    addressMap: False}
  testbench:      { container: testbench,  instanceType: testbench,     instGroup: allInstances,    addressMap: False} # self referential

# connections are specify interface connections between different instaces of objects
## - {}, dash followed by a dictionary, connections is a list of dictionaries
### interfacename: followed by string that is a key to this interface, an interface can be connected 1 or more times
### src: followed by a name of the source / master instance for this conneciton
### dst: followed by a name of the destination / slave instance for this conneciton
### count: followed by a number to indicate the number of ports to connect to, only valid with srcport or dstport and an interfacename that has multiple ports
###
### ports are optional, and are implied in most use cases. The exception is where disambiguation is needed, mainly in array use cases
### srcport: used if there is more than one objectname instance of the source / master, declares the port of source objectname to connect to
### dstport: used if there is more than one objectname instance of destination / slave, declares the port of destination objectname to connect to
### color: followed by a string which is a color (provide link to valid colors) this adds a color to diagrams
###          for this connection, optional (currently does not work in diagram generation code)
#connections:
#  - {interface: apbReg,           src: u_CPU,          dst: u_Top                    }   # this is the only apb register interface not generated as it is the root

# No connection map in testbench definition
#connectionMaps:
"""