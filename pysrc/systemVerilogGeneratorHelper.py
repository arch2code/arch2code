# systemVerilog Helper functions

from pathlib import Path
from pysrc.arch2codeHelper import printWarning

# Takes a file name f and a block b, checks if they match
#   returns a string of text modulename
def fileNameBlockCheck(f, b):
    out = ''
    if f != b:
        printWarning(f'The file name {f} does not match the block name {b}')
    out += f"//module as defined by block: {b}\n"
    out += f"module {b}\n"
    return out

# Takes a project file prj, a starting context sc, and a dictionary for code param passed in user defined packages up
#   excludeSelf is used to exclude self context references, used when importing packages inisde a package
#   returns a string of text that imports automatic packages and user defined packages
def importPackages(args, prj, sc, data, excludeSelf=False):
    out = ''
    moduleSelf = ''
    if excludeSelf:
        moduleSelf = Path(data['fileName']).stem
    
    packageList = []
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'package_sv'

    for context in data['includeContext']:
        if context in data['includeFiles'][fileMapKey]:
            packageName = data['includeFiles'][fileMapKey][context]['baseName']
            packageName = Path(packageName).stem
            # remove file extension, protect from multiple dots in file path / name
            # https://stackoverflow.com/a/45866399
            if not (packageName == moduleSelf and excludeSelf):
                packageList.insert(0, packageName)
    if packageList:
        out += f"// Generated Import package statement(s)\n"
        for item in packageList:
            out += f'import {item}::*;\n'
    if data['importPackages']:
        out += f"// User supplied Import package statement(s)\n"
        for item in data['importPackages'][0]:
            out += f'import {item}::*;\n'
            #out += f'export {item}::*;\n'
    return out
