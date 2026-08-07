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
    # clog2() in a generated width expression needs bitTwiddling.h. A module unit
    # takes it from its global module fragment (moduleScaffold moduleHeader)
    # instead, since an #include here would sit in the module purview.
    if fileMapKey != 'include_cppm' and data['usesClog2']:
        out.append('#include "bitTwiddling.h"')
    # take the list and return a string
    out.append("")
    return("\n".join(out))


def _file_map_key(args):
    # The firmware header names its key (`--fileMapKey=includeFW_hdr`); the
    # per-context module interface unit's region carries no key, so it is the only
    # unkeyed caller.
    return args.fileMapKey if args.fileMapKey else 'include_cppm'


def _include_context_modules(fileMapKey, prj, data):
    # In C++20 module-interface units (cppm) every `import` must
    # precede any other declaration in the module purview. With more
    # than one imported context the `using namespace` directives must
    # follow the import block, not be interleaved with it; collect
    # the two groups separately and concatenate. `others` is the textual-include
    # form, used by the firmware header, whose cross-context dependency is a
    # plain `#include` of the sibling *IncludesFW.h.
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
                imports.append(f'import {cpp_module_name(prj.contextModuleIdentity[name])};')
                usings.append(f'using namespace {cpp_namespace_name(prj.contextModuleIdentity[name])};')
            else:
                others.append(f'#include "{fileMap[name]["baseName"]}"')
    return imports + usings + others
