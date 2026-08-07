from pysrc.intf_gen_utils import cpp_module_name, cpp_block_module_name, cpp_base_module_name, cpp_namespace_name
import pysrc.intf_gen_utils as intf_gen_utils
from templates.systemc import structures
from templates.systemc.testbench import ext_module_header, ext_module_export, tb_module_header, tb_module_export

# The module interface units whose preamble moduleExport does NOT emit itself.
# `--fileMapKey` on a moduleExport region names the fileMap entry of the unit the
# preamble belongs to; absent means the block's own `<block>.cppm`. The
# testbench-family units select their own emitter because their module name,
# import set and excluded-DUT resolution are not a block's.
TB_MODULE_EXPORTS = {
    'tbExternal': ext_module_export,
    'testBench':  tb_module_export,
}

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # A module interface unit's header is split across two generated regions: the
    # GMF-only `moduleScaffold --section=<unit>ModuleHeader` region and the sibling
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
        case 'tbExternalModuleHeader':
            return ext_module_header(args, prj, data)
        case 'testBenchModuleHeader':
            return tb_module_header(args, prj, data)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are moduleHeader, blockModuleHeader, baseModuleHeader, tbExternalModuleHeader, testBenchModuleHeader")


def moduleHeader(args, prj, data):
    # Global module fragment + module declaration for a context's types module
    # (`<context>Includes.cppm`). An #include is legal only here, so this region
    # carries every header the file's later regions need, derived rather than
    # assumed:
    #   * systemc.h is the whole-file baseline - the struct regions name sc_bv /
    #     sc_trace, and a struct-less context's typedefs still need the uint*_t it
    #     supplies, so it is deliberately NOT gated on the structure set.
    #   * the struct-feature headers come from the same codeMapping/includeMapping
    #     the non-module header path uses, so the two cannot drift.
    #   * q_assert.h backs the struct round-trip test region's Q_ASSERT. The
    #     non-module path emits that include at its own point of use inside the
    #     test section, which a module unit cannot do.
    #   * bitTwiddling.h additionally backs clog2() in a generated width
    #     expression, which is independent of the struct set.
    hasStructures = len(data['structures']) > 0
    out = ['module;', '#include "systemc.h"']
    includes = structures.systemIncludes('module', 'headerIncludes', hasStructures)
    if hasStructures:
        includes.append('#include "q_assert.h"')
    if data['usesClog2']:
        includes.append('#include "bitTwiddling.h"')
    # The two sources of bitTwiddling.h overlap for a struct-bearing context that
    # also uses clog2, so the membership test is what collapses them - not a
    # defensive guard.
    for line in includes:
        if line not in out:
            out.append(line)
    out.append('')
    out.append(f'export module {cpp_module_name(data["contextModuleIdentity"])};')
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
    # non-modular shared header added there attaches to the global module rather
    # than the block module. Framework singletons such as endOfTestState are now
    # C++20 modules (`import a2c.endOfTest;`), added by hand in the `// user
    # imports here` preamble slot below, not included here.
    # The baseline is only what a generated line names: systemc.h for the
    # SC_MODULE/SC_HAS_PROCESS class and its sc_ port types, logging.h for the
    # generated `logBlock log_;` member. A block body's own Q_ASSERT, std::min or
    # clog2 is user content and belongs in the `// user #includes here` slot.
    baseline = [
        '#include "systemc.h"',
        '#include "logging.h"',
    ]
    deps = intf_gen_utils.sc_class_dependency_includes(prj, data)
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
    # A testbench-family unit names its fileMap key and supplies its own preamble.
    if args.fileMapKey in TB_MODULE_EXPORTS:
        return TB_MODULE_EXPORTS[args.fileMapKey](args, prj, data)
    # The COMPLETE module preamble for a parameterizable block's interface unit:
    # `export module <block>.block;` + every import, and NOTHING else: a
    # using-namespace would close the preamble here. Imports are illegal in the
    # global module fragment (blockModuleHeader), and every `import` must precede
    # the first non-import declaration, so the whole import set lives here while
    # the class region (classDecl / blockRegs) emits the using-directives at its
    # own head. That leaves the trailing `// user imports here` slot an open
    # preamble slot for a hand-authored import; a hand-added #include there closes
    # the preamble and attaches to this module. Emit order: the structural
    # dependency imports, then the contained-instance Base imports
    # (`import <child>.base;`, so the constructor body's createInstance /
    # dynamic_pointer_cast sees the complete child Base type), then the
    # interface-context imports beyond the structural set (a C++20 import is not
    # transitive, so the block body's unqualified spellings of types the base
    # pulls in need these re-imported here).
    deps = intf_gen_utils.sc_class_dependency_includes(prj, data)
    out = [f'export module {cpp_block_module_name(data["blockModuleName"])};']
    emitted = set()
    for kind, line in deps:
        emitted.add(line)
        if kind != 'import' or line.startswith('using namespace '):
            continue
        out.append(line)
    for line in intf_gen_utils.sc_instance_includes(data, prj):
        out.append(line)
    for context in data['includeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            for line in intf_gen_utils.cpp_context_include_lines(prj, context):
                if line in emitted:
                    continue
                emitted.add(line)
                if line.startswith('using namespace '):
                    continue
                out.append(line)
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
    deps = intf_gen_utils.sc_base_dependency_includes(prj, data)
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
