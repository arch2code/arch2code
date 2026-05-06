from pysrc.intf_gen_utils import module_name_from_include, namespace_name_from_include

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    fileMapKey = _file_map_key(args)
    if fileMapKey not in data['includeFiles']:
        out.append(f'Error {fileMapKey} must match option in project file')
    out.extend(_include_context_modules(fileMapKey, data))
    # Include bitTwiddling.h when any type in the accessible contexts uses clog2
    contexts = set(data['includeContext'].keys())
    if fileMapKey != 'include_cppm' and any(t['_context'] in contexts and (t['widthLog2'] != '' or t['widthLog2minus1'] != '')
           for t in prj.data['types'].values()):
        out.append('#include "bitTwiddling.h"')
    # take the list and return a string
    out.append("")
    return("\n".join(out))


def _file_map_key(args):
    if args.fileMapKey:
        return args.fileMapKey
    if args.mode == 'module':
        return 'include_cppm'
    return 'include_hdr'


def _include_context_modules(fileMapKey, data):
    out = list()
    for name in data['includeContext']:
        if name and name in data['includeFiles'][fileMapKey]:
            includeName = data['includeFiles'][fileMapKey][name]['baseName']
            if includeName != data['fileNameBase']:
                if fileMapKey == 'include_cppm':
                    out.append(f'import {module_name_from_include(includeName)};')
                    out.append(f'using namespace {namespace_name_from_include(includeName)};')
                else:
                    out.append(f'#include "{includeName}"')
    return out
