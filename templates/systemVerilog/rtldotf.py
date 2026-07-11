import os.path

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    incdirs = dict()
    for context in data['includeContext']:
        contextBasename = os.path.dirname(context)
        if contextBasename:
            contextBasename = './' + contextBasename
        else:
            contextBasename = '.'
        incdirs[contextBasename] = contextBasename
    for incdir, incdirName in incdirs.items():
        out.append(f'+incdir+{incdirName}')
        out.append(f'-y {incdirName}')
    
    for context in data['includeFiles'].get('package_sv', list()):
        # Emit only packages in this build's include-chain scope. A referenced
        # child project's standalone harness context is parsed into the same
        # database but is not on the build context's include chain, so it is not
        # part of the compiled design. Iterating the (DB-wide) package map in its
        # own order keeps the emitted order stable.
        if context not in data['includeContext']:
            continue
        contextBasename = os.path.dirname(context)
        if contextBasename:
            contextBasename += '/'
        packageName = data['includeFiles']['package_sv'][context]['baseName']
        out.append(f"{contextBasename}{packageName}")
    return '\n'.join(out)
