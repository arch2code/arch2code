from operator import truediv
from pysrc.arch2codeHelper import printError, warningAndErrorReport
import os
import argparse

# read source file and store in class
# process GENERATED_CODE_BEGIN & GENERATED_CODE_END and extract command line for use by the caller
# GENERATED_CODE_BEGIN allows a string following to be treated as a command line
# the indentation for the generated section is based on the comment delimiter for the GENERATED_CODE_BEGIN
#
# init creates sections list containing map with 'indent', 'command' keys
#   'indent' is current indentation to use for generating section
#   'command' contains inputs to parse
#   'lineNo' contains line number which had the command
#
# eg (assume @=spaces)
# @@@// GENERATED_CODE_BEGIN mycommand --param
# results in:
# self.sections()['indent'] = 3
# self.sections()['command'] = 'mycommand --param'
#
# process GENERATED_CODE_PARAM
# any string found after this is treated as global file level information processed
# and stored in params

class codeText:
    originalFileContents = None
    fileName = ""
    ungeneratedSections = list()
    sections = list()
    commentDelimiter = "//"
    block = None
    params = dict()
    def __init__(self, fileName, commentDelimiter="//") -> None:
        self.commentDelimiter = commentDelimiter
        self.fileName = fileName
        if not os.path.exists(fileName):
            printError(f"Unable to find {fileName}, {os.path.abspath(fileName)}")
            exit(warningAndErrorReport())

        with open(fileName, 'r') as f:
            self.originalFileContents = f.readlines()

        lines = self.originalFileContents
        currentSection = ""
        inGenerated = False # flag to track whether we are currently parsing lines between BEGIN-END
        lineNo = 0


        for line in lines:
            lineNo += 1
            pos = line.find("GENERATED_CODE_")
            if pos >=0:
                # we have a GENERATE_CODE_ on this line

                # copy the line with the GENERATED_CODE_ line to the output regardless
                currentSection += line

                # now we know where to start, convert the line into two pieces
                # one with the key and everything else
                genLine = line[pos:].strip().split(" ", 1)
                # handle all the cases
                if genLine[0]=="GENERATED_CODE_BEGIN":
                    indent = line.find(self.commentDelimiter)
                    assert (indent<pos) and (indent>=0), "Parse error missing comment delimiter"
                    # add the new generated section to the sections list with info for the caller to use
                    self.sections.append({'command': genLine[1], 'indent': indent, 'lineNo': lineNo})
                    self.template = genLine[1].split("=")[1] # capture template name
                    if inGenerated:
                        printError(f"Unexpected GENERATED_CODE_BEGIN in {fileName} line {lineNo}, check BEGIN END pairs")
                        exit(warningAndErrorReport())
                    inGenerated = True
                    # as we just transitioned to generated section, save everything accumulated so far and clear accumulation
                    self.ungeneratedSections.append(currentSection)
                    currentSection = ""

                elif genLine[0]=="GENERATED_CODE_END":
                    indent = line.find(self.commentDelimiter)
                    assert (indent<pos) and (indent>=0), "Parse error missing comment delimiter"
                    if not inGenerated:
                        printError(f"Unexpected GENERATED_CODE_END in {fileName} line {lineNo}, check BEGIN END pairs")
                        exit(warningAndErrorReport())
                    inGenerated = False

                elif genLine[0]=="GENERATED_CODE_PARAM":
                    if len(genLine) > 1:
                        self.parseParam(genLine[1])

                else:
                    #uh oh some unknown option
                    printError(f"Unexpected GENERATED_CODE_ in {fileName} line {lineNo} only BEGIN, END, PARAM allowed")
                    exit(warningAndErrorReport())
            else:
                if not inGenerated:
                    # lines outside of generated sections should be copied
                    currentSection += line
                # if we are in generated section we just discard
        if not inGenerated:
            self.ungeneratedSections.append(currentSection)
        else:
            printError(f"Unexpected end of file in {fileName} line {lineNo} GENERATED_CODE_END expected")
            exit(warningAndErrorReport())

    # this is the parser for GENERATED_CODE_PARAM lines. The use case is for file global configuration eg block to
    # prevent the need to duplicate on every input section
    def parseParam(self, cmdLine):
        parser = argparse.ArgumentParser(description="SystemC generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-b', '--block', type=str, help='Block name' )
        parser.add_argument('--context', action='append', type=str, help='Yaml file context for generation' )
        parser.add_argument('--scope', type=str, help='hierarchy scope eg top' )
        parser.add_argument('--variant', type=str, help='Block variant name' )
        parser.add_argument('--importPackages', default=[], nargs='+', action='append', help='SystemVerilog only, this is a list that defines all packages to import')
        parser.add_argument('--mode', type=str, default='', help='File level mode option' )
        parser.add_argument('--project', default=[], nargs='+', help='List of projects that this file belongs to if no match ignore file' )
        parser.add_argument('--hierarchy', action='store_true', help='generate in hierarchy mode' )
        parser.add_argument('--inst', type=str, help='instance name' )

        self.params = parser.parse_args(cmdLine.split(' '))
        self.block = self.params.block
        if not self.params:
            print (f"params empty cmdLine{cmdLine}")


    def genFile(self, genList):
        # reverse the list so we get everything in the right order
        self.ungeneratedSections.reverse()
        if len(genList) != len(self.sections):
            printError(f"Incomplete generation, expected {len(self.sections)} got {len(genList)}")
            exit(warningAndErrorReport())
        newFile = self.ungeneratedSections.pop()
        for section in genList:
            newFile += section + '\n' + self.ungeneratedSections.pop()

        if newFile != "".join(self.originalFileContents):
            with open(self.fileName, 'w') as f:
                f.writelines(newFile)



