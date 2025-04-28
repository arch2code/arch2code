# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    if args.fileMapKey not in data['includeFiles']:
        out.append(f'Error {args.fileMapKey} must match option in project file\n')
    for name in data['includeContext']:
        if name and name in data['includeFiles'][args.fileMapKey]:
            includeName = data['includeFiles'][args.fileMapKey][name]['baseName']
            if includeName != data['fileNameBase']:
                out.append(f'#include "{includeName}"\n')
    # take the list and return a string
    return("".join(out))
