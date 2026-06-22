from pysrc.intf_gen_utils import cpp_module_name, cpp_namespace_name

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    fileMapKey = _file_map_key(args)
    out.extend(_include_context_modules(fileMapKey, prj, data))
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


def _include_context_modules(fileMapKey, prj, data):
    # In C++20 module-interface units (cppm) every `import` must
    # precede any other declaration in the module purview. With more
    # than one imported context the `using namespace` directives must
    # follow the import block, not be interleaved with it; collect
    # the two groups separately and concatenate.
    imports = list()
    usings = list()
    others = list()
    fileMap = data['includeFiles'].get(fileMapKey, {})
    currentContext = data['context']
    for name in data['includeContext']:
        if name and name in fileMap:
            if name == currentContext:
                continue
            if fileMapKey == 'include_cppm':
                imports.append(f'import {cpp_module_name(prj.includeName[name])};')
                usings.append(f'using namespace {cpp_namespace_name(prj.includeName[name])};')
            else:
                others.append(f'#include "{fileMap[name]["baseName"]}"')
    return imports + usings + others
