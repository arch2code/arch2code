import pysrc.arch2codeGlobals as globals
from collections.abc import Mapping
from pathlib import Path
from colorama import Fore, Back, Style
import math

import traceback

def clog2(x):
  return math.ceil(math.log2(x))

def roundup_pow2(n):
    return 2**clog2(n)

def roundup_pow2min4(n):
    return max(2**clog2(n), 4)


def roundup_multiple(x, n):
    return -(-x // n) * n

def printIfDebug(instring):
    if(globals.debug):
        print(instring)

def confirmConnection(inDictionary, interfaceKey, src, dst):
    connectionsDictionary = inDictionary.get('connections')
    for list in connectionsDictionary:
        if (list['interfaceKey'] == interfaceKey and list['src'] == src and list['dst'] == dst):
            return True
    printError(f"The interfaceKey {interfaceKey} with source {src} and destination {dst} can not be found.")
    return False

import subprocess

# TODO to remove subprocess and never create output svg files a build option would be needed to create the flow diagrams
#       alternatively the svg outputs can be created at the end of this function if no errors, save processing time
# TODO proccess each flow as a seperate diagram
# TODO replace instance names with object names? Or append then together?
### add option for path indicator --> ->, could consider a required field, no need with latest style
def makeFlows(inDictionary):
    flows = inDictionary.get('flows')
    for item in flows['filenames']:
        printIfDebug(item)
        fileHandleRead  = open(item, 'r')
        fileName = Path(item).stem
        flowTextLines = ''
        lineNumber = 1
        for line in fileHandleRead:
            printIfDebug(line[:-1])
            if ("'''process'''" in line and not line.startswith('\'')):
                words = line.split()
                if (len(words) != 6):
                    errorString = f"In file {item} at line {lineNumber}\n" \
                                  "To do plant uml connection replacement the format must match the following:\n" \
                                  " instance operator instance : connectionKey '''process'''\n" \
                                  "For example:\n" \
                                  " u_blocka -> u_blockc0 : cs_stuff '''process'''"
                    printError(errorString)
                if (confirmConnection(inDictionary, words[4], words[0], words[2])):
                    # do line repacement
                    flowTextLines += f'{words[0]} {words[1]} {words[2]} {words[3]} {words[4]}\n' # TODO optionally add structure name, TODO optionally add all variables, TODO consider doing 3 flows one with interface, one with interface and structure, one with interface and variables
                else:
                    # write original file to output file
                    flowTextLines += f'{line[:-1]} Error! bad connection declaration\n'
            else:
                flowTextLines += line
            lineNumber += 1
        fileHandleRead.close()
        Path(globals.pudir).mkdir(parents=True, exist_ok=True)
        (Path(globals.pudir, f'{fileName}.pu')).write_text(flowTextLines)

    #for k,v in flows.items():
    #    # each key is a flow and each value is a list of lines
    #    flowTextLines = '@startuml\n'
    #    for l in v:
    #        if (isinstance(l, list)):
    #            # this means it is a connection reference and should be tested for consistency errors
    #            #   optionally we could add in structures
    #            #   optionally we could add in different -> --> options
    #            if (confirmConnection(inDictionary, l[0], l[1], l[2])):
    #                flowTextLines += f'{l[1]} -> {l[2]}: {l[0]}\n'
    #        else:
    #            # this means this line item in the flow is a raw platnum item like a note, alt, loop, or end
    #            flowTextLines += f'{l}\n'
    #    flowTextLines += '@enduml\n'
    #    Path(globals.pudir).mkdir(parents=True, exist_ok=True)
    #    (Path(globals.pudir, globals.filename+'_{}.pu'.format(k))).write_text(flowTextLines)

    # This is going to make all in one swoop in the directory globals.pudir
    subprocess.run(['java', '-jar', f'{globals.pujar}/plantuml.jar', '-tsvg', f'{globals.pudir}'])

## This plantuml library does not seem to work, tested version 0.3.0
#from plantuml import PlantUML
#
#def testPlantUML():
#    # create a string and put it in a file descriptor
#    # execute puml on file descriptor
#    filenamewithpath = globals.pudir/globals.filename.with_suffix('.pu')
#    #Path(filenamewithpath).mkdir(parents=True, exist_ok=True)
#    #exit()
#    #f = open(filenamewithpath.mkdir(parents=True, exist_ok=True), 'w+')
#    filenamewithpath.mkdir(parents=True, exist_ok=True)
#    #f = open(filenamewithpath, 'w+')
#    f = open('pu_out/test.pu', 'w+')
#    #f.write('@startuml\ntitle Test Flow\nAlice->Bob: Do something\nnote right of Bob: Bob will try\nBob->Alice: I did it!!\n@enduml\nlicense')
#    f.write('@startuml\ntitle Test Flow\nAlice->Bob: Do something\nnote right of Bob: Bob will try\nBob->Alice: I did it!!\n@enduml')
#    #PlantUML(f)
#    #PlantUML(url='http://www.plantuml.com/plantuml/img/').processes_file(f)
#    PlantUML(url='http://www.plantuml.com/plantuml/img/').processes_file('pu_out/test.pu')

def warningAndErrorReport():
    returnValue = 0
    if (globals.warningCount > 0):
        if (globals.warningCount == 1):
            s = 'Warning'
        else:
            s = 'Warnings'
        if globals.disableColors:
            print(f'Found {globals.warningCount} '+s+'.')
        else:
            print(Fore.YELLOW + f'Found {globals.warningCount} '+s+'.')
    if (globals.errorCount > 0):
        returnValue = globals.errorCount
        if (globals.errorCount == 1):
            s = 'Error'
        else:
            s = 'Errors'
        if globals.disableColors:
            print(f'Found {globals.errorCount} '+s+'.')
        else:
            print(Fore.RED + f'Found {globals.errorCount} '+s+'.')
    return returnValue

def printError(inString):
    globals.errorCount +=1
    if globals.disableColors:
        print(f'Error Number {globals.errorCount}:')
        print(f'{inString}')
    else:
        print(Fore.RED + f'Error Number ' + Style.RESET_ALL + Back.RED + f'{globals.errorCount}' + Style.RESET_ALL + Fore.RED + ':')
        print(Fore.RED + f'{inString}')

def printWarning(inString):
    globals.warningCount +=1
    if globals.disableColors:
        print(f'Warning Number {globals.warningCount}:')
        print(f'{inString}')
    else:
        print(Fore.YELLOW + f'Warning Number ' + Style.RESET_ALL + Back.YELLOW + f'{globals.warningCount}' + Style.RESET_ALL + Fore.YELLOW + ':')
        print(Fore.YELLOW + f'{inString}')

def printTracebackStack():
    traceback.print_stack()