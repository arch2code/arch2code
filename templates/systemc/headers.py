# args from generator line
# prj object
# data set dict
import os


def _resolve_context_key(prj, ctx_arg):
    """Map GENERATED_CODE_PARAM --context= value to a key in prj.includeName."""
    if ctx_arg in prj.includeName:
        return ctx_arg
    for k in prj.includeName:
        if ctx_arg == os.path.basename(k) or ctx_arg in os.path.basename(k):
            return k
    return ctx_arg


def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    if args.fileMapKey not in data['includeFiles']:
        out.append(f'Error {args.fileMapKey} must match option in project file')
    included_ns = []
    for name in data['includeContext']:
        if name and name in data['includeFiles'][args.fileMapKey]:
            includeName = data['includeFiles'][args.fileMapKey][name]['baseName']
            if includeName != data['fileNameBase']:
                out.append(f'#include "{includeName}"')
                included_ns.append(prj.includeName[name] + '_ns')
    # Include bitTwiddling.h when any type in the accessible contexts uses clog2
    contexts = set(data['includeContext'].keys())
    if any(t['_context'] in contexts and (t['widthLog2'] != '' or t['widthLog2minus1'] != '')
           for t in prj.data['types'].values()):
        out.append('#include "bitTwiddling.h"')
    # Mirror SV package: wrap shared types in a context namespace; import deps via using
    if args.fileMapKey == 'include_hdr':
        ctx_list = getattr(args, 'context', None)
        if ctx_list:
            ctx_key = _resolve_context_key(prj, ctx_list[0])
            if ctx_key in prj.includeName:
                current_ns = prj.includeName[ctx_key] + '_ns'
                out.append(f'namespace {current_ns} {{')
                for ns in dict.fromkeys(included_ns):
                    out.append(f'    using namespace {ns};')
    # take the list and return a string
    out.append("")
    return("\n".join(out))
