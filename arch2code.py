#!/usr/bin/env python3
import argparse
from ruamel.yaml import YAML
from colorama import init, Fore, Back, Style

# Imports from arch2code project (local imports)
#   pysrc directory is the one package so far for arch2code
#       contains globals, helper, processYaml, and docgen
import pysrc.arch2codeGlobals as globals
from pysrc.arch2codeHelper import makeFlows, printError, printIfDebug, printWarning, warningAndErrorReport
from pysrc.processYaml import projectCreate, projectOpen
from pysrc.displayInstance import displayInstancesDiagram
from pysrc.drawStructure import drawStructure
from pysrc.docgen import makeDoc
from pysrc.systemcGen import genSystemC
from pysrc.systemVerilogGenerator import systemVerilogGenerator
from pysrc.initialSystemVerilogPackagesGenerator import initialSystemVerilogPackagesGenerator
from pysrc.documentGenerator import documentGenerator
from pysrc.newModule import newModule
from pysrc.newProject import newProject

title=('Arch2Code is a tool to describe an architecture in yaml. The architecture includes structures, '
       'interfaces, instances of modules and connectivity between instances. From the description generate output '
       'for documentation, SystemVerilog, and SystemC.'
       'For more details see https://docs.arch2code.org/a2c-docs/latest/index.html'
       )
# TODO put command line usage examples in the epilog
epilog=('epilog TODO: put command line usage examples here.')

parser = argparse.ArgumentParser(description=title, formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog=epilog)
# common options
parser.add_argument('-y', '--yaml', type=str, help='Path to input yaml file.', default="")
parser.add_argument('--db', type=str, help='Path to db file.', default="")
parser.add_argument('-r', '--readonly', action='store_true', help='Open db in read only mode')
parser.add_argument('-d', '--debug', '--verbose', action='store_true', help='Increase verbosity of debug output.')
parser.add_argument('--file', type=str, help='File for code generation (SystemC & Verilog)')
parser.add_argument('-v', '--version', action='store_true', help='arch2code (a2c) version or revision.')

# modes of operation
parser.add_argument('--diagram', action='store_true', help='Create the Instances Diagram. If run with --debug the diagram will be opened for preview.')
parser.add_argument('--docgen', action='store_true', help='runs document generator')
parser.add_argument('--systemVerilogGenerator', '-sv', action='store_true', help='runs the SystemVerilog generator')
parser.add_argument('--initialSystemVerilogPackagesGenerator', '-isvp', action='store_true', help='Automatically creates systemVerilog Packages\
                        creates a package per context. If a yaml context is at my.yaml the package will be created\
                        at a path delcared by --moduledir the package will be named myPackage.sv. If an included package of\
                        my.yaml is at a/a.yaml relative to the top my.yaml context then output package will be in the directory\
                        indicated by --moduledir then a/aPackage.sv.')
parser.add_argument('--systemc', '-sc', action='store_true', help='runs SystemC generator')
parser.add_argument('--newmodule', action='store_true', help='create all the base files for a new module')
parser.add_argument('--newproject', action='store_true', help='create a new project')

# diagram options
parser.add_argument('--drawStructure', type=str, help='Takes the path to a structure in the form context.structureName')
parser.add_argument('-dof', '--diagramOutFilename', type=str, help='Used to set the diagram output filename.')
parser.add_argument('-dod', '--diagramOutDirectory', type=str, help='Used to set the diagram output directory loacation.')
parser.add_argument('--bgcolor', type=str, help='Used to set background color for diagrams, transparent, white, black, grey, etc', default=globals.bgcolor)
parser.add_argument('-ddgv','--diagramDeleteGV', action='store_true', help='This option removes the diagram .gv file, the intermediate graphviz text file.\
                                                                             If set the output svg will be filename.svg, if unset the svg will be filename.gv.svg.')
parser.add_argument('--diagramNoConnections', action='store_true', help='In order to help debug connectivity issues this options creates the Instances\
                                                                          Diagram without connections. If run with --debug the diagram will be opened\
                                                                          for preview.')
parser.add_argument('--flows', action='store_true', help='Create all specified flows. This will run plantuml\'s java application and might be slower than\
                                                            the Instances Diagram.')
parser.add_argument('--colors', nargs="+", type=str, help='Specify the color pallete to use for structures, if `--color white` is used no colors used on bits.  All\
                                                            color lists with more than one color will use rotating colors. For some retro colors\
                                                            try `--colors lightblue lawngreen violet orange deeppink yellow`. The default will restart the color\
                                                            scheme every 8 bits to easily visualize the byte boundaries. Four colors would highlight nibbles.',
                             default=globals.colors)
parser.add_argument('-ibt', '--instancesWithBlockType', action='store_true', help='Prints out defined instances and the block type of that instance')
parser.add_argument('-bc', '--blockContexts', action='store_true', help='Given a block prints out all defined contexts for that block in the design,\
                                                                           used to help build systemVerilog pakcages')
# docgen options
parser.add_argument('--docout', type=str, help='Document output file', default='arch.txt')
parser.add_argument('--instance', type=str, help='Instance to document, if omitted defaults to the top level', default=globals.defaultInstance)
parser.add_argument('--depth', type=int, help='Depth to document, 1=instance block definition and contained instances, but no details of contained instances ', default=1)

# systemc options
parser.add_argument('--instances', type=str, help='A list of instances in the design to be used with --systemc or --systemVerilogGenerator. If omitted, all instance are used')

# newmodule options
parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')


args = parser.parse_args()
globals.debug    = args.debug
globals.bgcolor  = args.bgcolor
globals.deleteGV = args.diagramDeleteGV
# Disable colors if NO_COLOR environment variable is set (useful for tests)
import os
globals.disableColors = os.environ.get('NO_COLOR', '').lower() in ('1', 'true', 'yes')
if args.yaml == "" and args.db == "":
    if args.newproject:
        newProject(args)
    else:
        printError("Must specify either a yaml file or a db file.")
    exit(warningAndErrorReport())
if args.db != "" and args.yaml == "":
    args.readonly = True
elif args.db == "" and args.yaml != "":
    printError("Must specify file path to create db from yaml")
    exit(warningAndErrorReport())

if args.version:
    if args.readonly:
        # readonly and version prints only version with no colors for builds and scripting
        print(f"{globals.version}")
    else:
        print(f"arch2code version: "+Back.BLACK+Fore.LIGHTGREEN_EX+f"{globals.version}"+Style.RESET_ALL)
    exit(warningAndErrorReport())

if args.readonly:
    printIfDebug("readonly")
    prj = projectOpen(args.db)
else:
    prj = projectCreate(args.yaml, args.db)

if (args.diagram or args.diagramNoConnections or args.drawStructure):
    if (args.diagramOutFilename):
        globals.filename = args.diagramOutFilename
    else:
        globals.filename = prj.config.getConfig('PROJECTNAME')
    if (args.diagramOutDirectory):
        globals.gvdir = args.diagramOutDirectory

# Initialize colorama for warning and error prints
init(autoreset=True)

if (args.diagram or args.diagramNoConnections):
    displayInstancesDiagram(prj, args.instance, args.depth, args.diagramNoConnections)
if (args.drawStructure):
    drawStructure(prj, args.drawStructure, args.colors)
if (args.flows):
    s = 'The --flows option currently is not supported until A2C-28 is addressed.'
    s = s+'\nSee https://arch2code.atlassian.net/browse/A2C-28 for more details'
    printError(s)
    #makeFlows() # stays as a reminder to which function needs updating / replacing
if (args.docgen and args.file):
    if not args.diagramOutDirectory:
        printError("Must specify a diagramOutDirectory")
        exit(warningAndErrorReport())
    else:
        globals.gvdir = args.diagramOutDirectory
        documentGenerator(prj, args)
elif (args.docgen):
    myDoc = makeDoc(prj, args)
if (args.systemc):
    genSystemC(prj, args)
if (args.systemVerilogGenerator):
    systemVerilogGenerator(prj, args)
if (args.newmodule):
    newModule(prj, args)
if (args.instancesWithBlockType):
    for k, v in prj.instances.items():
        c = []
        for k2, v2 in prj.yamlContext[prj.data['instances'][v]['_context']].items():
            c.insert(0, k2)
        print(Back.BLACK+Fore.WHITE+f"Instance: "+Fore.CYAN+f"{k}"+Fore.WHITE+f" of block type " \
              +Fore.LIGHTGREEN_EX+f"{prj.data['instances'][v]['instanceType']}"+Fore.WHITE \
              +f" with context(s): "+f"{c}"+Style.RESET_ALL)
if (args.initialSystemVerilogPackagesGenerator):
    initialSystemVerilogPackagesGenerator(prj, args)
if (args.blockContexts):
    for k, v in prj.instances.items():
        print(Back.BLACK+Fore.WHITE+f"Instance: "+Fore.CYAN+f"{k}"+Fore.WHITE+f" with contexts" \
               +f": "+f"{prj.getContexts(k)}"+Style.RESET_ALL)

exit(warningAndErrorReport())