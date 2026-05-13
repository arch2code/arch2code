from pysrc.intf_gen_utils import module_name_from_include, namespace_name_from_include

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    fileMapKey = _file_map_key(args)
    # Some legacy generated regions still request retired include maps
    # (for example include_hdr after a context moved to include_cppm).
    # Treat the missing map as an empty include set; generation should not
    # emit diagnostic text into C++ output.
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
    # In C++20 module-interface units (cppm) every `import` must
    # precede any other declaration in the module purview. With more
    # than one imported context the `using namespace` directives must
    # follow the import block, not be interleaved with it; collect
    # the two groups separately and concatenate.
    imports = list()
    usings = list()
    others = list()
    fileMap = data['includeFiles'].get(fileMapKey, {})
    if not fileMap and fileMapKey == 'include_hdr':
        # Legacy generated headers may still request include_hdr after the
        # project moved context includes to C++20 module interfaces. The
        # sibling .h files still exist for non-module compilation paths, so
        # derive their names from the active include_cppm map.
        fileMap = {
            name: {
                **info,
                'baseName': info['baseName'].removesuffix('.cppm') + '.h',
            }
            for name, info in data['includeFiles'].get('include_cppm', {}).items()
        }
    for name in data['includeContext']:
        if name and name in fileMap:
            includeName = fileMap[name]['baseName']
            if includeName != data['fileNameBase']:
                if fileMapKey == 'include_cppm':
                    imports.append(f'import {module_name_from_include(includeName)};')
                    usings.append(f'using namespace {namespace_name_from_include(includeName)};')
                else:
                    others.append(f'#include "{includeName}"')
    return imports + usings + others
