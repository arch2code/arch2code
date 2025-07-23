import os.path

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    incdirs = set()
    for context in data['includeContext']:
        contextBasename = os.path.dirname(context)
        if contextBasename:
            contextBasename += './'
        else:
            contextBasename = '.'
        incdirs.add(contextBasename)
    for incdir in incdirs:
        out.append(f'+incdir+{incdir}')
    for context in data['includeFiles']['package_sv']:
        contextBasename = os.path.dirname(context)
        if contextBasename:
            contextBasename += '/'
        packageName = data['includeFiles']['package_sv'][context]['baseName']
        out.append(f"{contextBasename}{packageName}")
    return '\n'.join(out)
