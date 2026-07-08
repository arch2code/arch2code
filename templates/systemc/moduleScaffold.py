from pysrc.intf_gen_utils import cpp_module_name, cpp_block_module_name, cpp_base_module_name, cpp_namespace_name
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
        case 'baseModuleHeader':
            return baseModuleHeader(args, prj, data)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are moduleHeader, blockModuleHeader, baseModuleHeader")


def moduleHeader(args, prj, data):
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "bitTwiddling.h"',
        '#include "q_assert.h"',
        '#include <algorithm>',
        '',
        f'export module {cpp_module_name(data["contextModuleIdentity"])};',
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
    out.append('')
    out.append(f'export module {cpp_block_module_name(data["blockName"])};')
    # All import declarations must immediately follow the module declaration,
    # before any other declaration (e.g. a using-namespace); the language rejects
    # an `import` that trails a using-namespace. Emit every import first — context
    # imports, then contained-instance Base imports — and defer the context
    # `using namespace` lines until after them. Contained-instance Base modules
    # (`import <child>.base;`) let the constructor body's createInstance /
    # dynamic_pointer_cast see the complete child Base type; imports are illegal
    # in the global module fragment so they live here in the purview.
    usings = []
    for kind, line in deps:
        if kind != 'import':
            continue
        if line.startswith('using namespace '):
            usings.append(line)
        else:
            out.append(line)
    for line in intf_gen_utils.sc_instance_includes(data, prj):
        out.append(line)
    out.extend(usings)
    return "\n".join(out)


def baseModuleHeader(args, prj, data):
    # Global module fragment + module declaration for a block's Base/Inverted/
    # Channels interface unit (`<block>Base.cppm`, `export module <block>.base;`).
    # The GMF carries the SystemC baseline plus baseClassDecl's dependency
    # #includes (shared via sc_base_dependency_includes); the context types
    # module the base imports is re-stated as `import <types>;` after the module
    # declaration. baseClassDecl suppresses all of these in module mode so they
    # live here exactly once.
    baseline = [
        '#include "systemc.h"',
    ]
    deps = intf_gen_utils.sc_base_dependency_includes(args, prj, data)
    out = ['module;']
    emitted = set()
    for line in baseline:
        out.append(line)
        emitted.add(line)
    for kind, line in deps:
        if kind == 'include' and line not in emitted:
            out.append(line)
            emitted.add(line)
    out.append('')
    out.append(f'export module {cpp_base_module_name(data["blockName"])};')
    # All import declarations must immediately follow the module declaration,
    # before any other declaration (e.g. a using-namespace); emit the context
    # imports first and defer their `using namespace` lines after them.
    usings = []
    for kind, line in deps:
        if kind != 'import':
            continue
        if line.startswith('using namespace '):
            usings.append(line)
        else:
            out.append(line)
    out.extend(usings)
    return "\n".join(out)
