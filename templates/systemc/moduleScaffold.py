from pysrc.intf_gen_utils import cpp_module_name, cpp_block_module_name, cpp_base_module_name, cpp_namespace_name
import pysrc.intf_gen_utils as intf_gen_utils

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # A block-module header is split across two generated regions: the GMF-only
    # `moduleScaffold --section=blockModuleHeader` region and the sibling
    # `moduleExport` region (its own template name, no --section) that owns the
    # `export module` declaration plus every import. Dispatch moduleExport off the
    # template name; the remaining scaffolds select on --section.
    if args.template == 'moduleExport':
        return moduleExport(args, prj, data)
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
    # Global module fragment ONLY for a parameterizable block's own interface unit
    # (`<block>.cppm`). This region ends BEFORE `export module` — the declaration
    # and every import live in the sibling `moduleExport` region. The GMF carries
    # the SystemC baseline plus the block class's dependency #includes (shared
    # with classDecl via sc_class_dependency_includes). Only #includes are legal
    # here (global module fragment); classDecl suppresses all of these in module
    # mode so they live here exactly once. The trailing `// user #includes here`
    # user slot sits after this region's end, in the same GMF zone, so a
    # non-modular shared header (e.g. endOfTest.h) added there attaches to the
    # global module rather than the block module.
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
    return "\n".join(out)


def moduleExport(args, prj, data):
    # `export module <block>.block;` plus every import for a parameterizable
    # block's interface unit. Imports are illegal in the global module fragment
    # (blockModuleHeader), so they all live here in the module preamble. Every
    # `import` must precede the first non-import declaration, and a using-namespace
    # permanently closes the preamble. For a classDecl-rendered block this region
    # emits imports ONLY — the context `using namespace` lines are relocated to the
    # head of the classDecl region (templates/systemc/classDecl.py). That keeps
    # this region import-only so the trailing `// user imports here` user slot
    # inherits an open preamble where a hand-added `import` stays legal. A
    # reg-handler block is the exception: its class is rendered by the blockRegs
    # template, which does not re-emit the usings, so they ride at the TAIL of this
    # region (after the imports, before the region end). Emit context imports
    # first, then contained-instance Base imports (`import <child>.base;`), which
    # let the constructor body's createInstance / dynamic_pointer_cast see the
    # complete child Base type.
    deps = intf_gen_utils.sc_class_dependency_includes(args, prj, data)
    out = [f'export module {cpp_block_module_name(data["blockModuleName"])};']
    isRegHandler = data['blockInfo']['isRegHandler']
    usings = []
    for kind, line in deps:
        if kind != 'import':
            continue
        if line.startswith('using namespace '):
            if isRegHandler:
                usings.append(line)
            continue
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
    out.append(f'export module {cpp_base_module_name(data["blockModuleName"])};')
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
