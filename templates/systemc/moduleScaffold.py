from pysrc.intf_gen_utils import cpp_module_name, cpp_block_module_name, cpp_namespace_name
import pysrc.intf_gen_utils as intf_gen_utils

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'moduleHeader':
            return moduleHeader(args, prj, data)
        case 'blockModuleHeader':
            return blockModuleHeader(args, prj, data)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are moduleHeader, blockModuleHeader")


def moduleHeader(args, prj, data):
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "bitTwiddling.h"',
        '#include "q_assert.h"',
        '#include <algorithm>',
        '',
        f'export module {cpp_module_name(data["contextIncludeName"])};',
    ]
    return "\n".join(out)


def blockModuleHeader(args, prj, data):
    # Global module fragment + module declaration for a parameterizable block's
    # own interface unit (`<block>.cppm`, `export module <block>.block;`). The
    # GMF carries the SystemC baseline plus the block class's dependency
    # #includes (shared with classDecl via sc_class_dependency_includes); the
    # context types module the block imports is re-stated as `import <types>;`
    # after the module declaration. classDecl suppresses all of these in module
    # mode so they live here exactly once.
    baseline = [
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "bitTwiddling.h"',
        '#include "q_assert.h"',
        '#include <algorithm>',
    ]
    deps = intf_gen_utils.sc_class_dependency_includes(args, prj, data)
    out = ['module;']
    emitted = set()
    for line in baseline:
        out.append(line)
        emitted.add(line)
    for kind, line in deps:
        if kind == 'include' and line not in emitted:
            out.append(line)
            emitted.add(line)
    # Contained-instance Base headers. In classic mode these live in the
    # constructor's init section, but module mode forbids #include after the
    # module declaration, so a container module carries them in the GMF where
    # the constructor body's createInstance / dynamic_pointer_cast needs the
    # complete child Base type.
    for line in intf_gen_utils.sc_instance_includes(data, prj):
        if line not in emitted:
            out.append(line)
            emitted.add(line)
    out.append('')
    out.append(f'export module {cpp_block_module_name(data["blockName"])};')
    for kind, line in deps:
        if kind == 'import':
            out.append(line)
    return "\n".join(out)
