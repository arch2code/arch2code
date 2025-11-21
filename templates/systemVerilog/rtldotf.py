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
        contextBasename = os.path.dirname(context)
        if contextBasename:
            contextBasename += '/'
        packageName = data['includeFiles']['package_sv'][context]['baseName']
        out.append(f"{contextBasename}{packageName}")
    return '\n'.join(out)
