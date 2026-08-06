# systemVerilog Helper functions

# Emits the module declaration header from the block name. The filename/block
# consistency check is performed by the SystemVerilog generator before rendering,
# not here, so this helper never inspects the output filename.
def moduleDeclaration(b):
    return f"//module as defined by block: {b}\nmodule {b}"

# Takes a project file prj, a starting context sc, and a dictionary for code param passed in user defined packages up
#   excludeSelf is used to exclude self context references, used when importing packages inside a package
#   returns a string of text that imports automatic packages and user defined packages
def importPackages(args, prj, sc, data, excludeSelf=False):
    out = []
    packageList = []
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'package_sv'

    for context in data['includeContext']:
        if context in data['includeFiles'][fileMapKey]:
            # excludeSelf drops the starting context's own package when a
            # package imports its sibling packages.
            if excludeSelf and context == sc:
                continue
            packageName = prj.contextModuleIdentity[context] + '_package'
            packageList.insert(0, packageName)
    if packageList:
        out.append(f"// Generated Import package statement(s)")
        for item in packageList:
            out.append(f'import {item}::*;')
    if data['importPackages']:
        out.append(f"// User supplied Import package statement(s)")
        for item in data['importPackages'][0]:
            out.append(f'import {item}::*;')
            #out.append(f'export {item}::*;')
    return "\n".join(out)
