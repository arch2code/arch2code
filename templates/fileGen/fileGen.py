
from jinja2 import Template as J2Template
from string import Template
import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.intf_gen_utils import FW_NAMESPACE
from pysrc.genFileParam import contextParamTail, contextParamMode
from pysrc.arch2codeHelper import printError, warningAndErrorReport

# Redefine the pattern to follow the format defined by dvt templates (i.e __name__, or __{name}__)
class TemplateCustom(Template):
    delimiter = '__'
    pattern = r'''
    __(?:
    (?P<escaped>__)|
    (?P<named>[a-zA-Z][a-zA-Z0-9]*(_?[a-zA-Z0-9])*)|
    {(?P<braced>[a-zA-Z][a-zA-Z0-9]*(_?[a-zA-Z0-9])*)}|
    (?P<invalid>))__
    '''

# this file is used to create blank files for a new module with sections required
def render(args, prj, data):
    isRegHandler = True if 'block' in data and next(filter(lambda x: x['block'] == data['block'] and x['isRegHandler'] == 1, prj['blocks'].values()), None) else False
    # An APB-router block declares an addressBlock: section; its RTL is fully
    # emitted by the apbDecodeModule template (module header through endmodule),
    # so it scaffolds without the trailing endmodule rtlModule adds.
    isApbRouter = True if 'block' in data and next(filter(lambda x: x['block'] == data['block'] and x.get('addressBlock'), prj['blocks'].values()), None) else False
    match data['target']:
        case 'blockBase_cppm':
            return(blockBase_cppm(args, prj, data))
        case 'blockBase_src':
            return(blockBase_src(args, prj, data))
        case 'block_hdr':
            if isRegHandler:
                return(blockRegs_hdr(args, prj, data))
            else:
                return(block_hdr(args, prj, data))
        case 'block_src':
            if isRegHandler:
                return(blockRegs_src(args, prj, data))
            else:
                return(block_src(args, prj, data))
            return(block_src(args, prj, data))
        case 'blockModule_cppm':
            if isRegHandler:
                return(blockRegsModule_cppm(args, prj, data))
            else:
                return(blockModule_cppm(args, prj, data))
        case 'blockRegistrar_cppm':
            return(blockRegistrar_cppm(args, prj, data))
        case 'blockVlRegistrar_src':
            return(blockVlRegistrar_src(args, prj, data))
        case 'foreignConfig_cppm':
            return(foreignConfig_cppm(args, prj, data))
        case 'vlSvWrapForeign_sv':
            return(vlSvWrapForeign_sv(args, prj, data))
        case 'rtlModule_sv':
            if isRegHandler:
                return(rtlModuleRegs(args, prj, data))
            elif isApbRouter:
                return(rtlModuleApbDecode(args, prj, data))
            else:
                return(rtlModule(args, prj, data))
        case 'vlSvWrap_sv':
            return(vlSvWrap_sv(args, prj, data))
        case 'vlSvWrapBody_svh':
            return(vlSvWrapBody_svh(args, prj, data))
        case 'vlScWrap_hdr':
            return(vlScWrap_hdr(args, prj, data))
        case 'vlSvWrap_svVariant':
            return(vlSvWrap_sv(args, prj, data))
        case 'tandem_hdr':
            return(tandem_hdr(args, prj, data))
        case 'tandem_src':
            return(tandem_src(args, prj, data))
        case 'tbConfig_src':
            return(tbConfig(args, prj, data))
        case 'testBench_cppm':
            return(testBench_cppm(args, prj, data))
        case 'tbExternal_cppm':
            return(tbExternal_cppm(args, prj, data))
        case 'include_cppm':
            return(include_cppm(args, prj, data))
        case 'config_hdr':
            return(config_hdr(args, prj, data))
        case 'includeFW_src':
            return(includeFW_src(args, prj, data))
        case 'includeFW_hdr':
            return(includeFW_hdr(args, prj, data))
        case 'package_sv':
            return(package_sv(args, prj, data))
        case 'rtlDotF_f':
            return(rtlDotF_f(args, prj, data))
        # Exhaustive over the `<fileType>_<ext>` keys a fileMap can name. An
        # unregistered key must abort NON-ZERO: newModule scaffolds the remaining
        # artifacts after this call, so a zero status would truncate the scaffold
        # while `make newmodule` still reported success.
        case _:
            printError(f"fileMap file key '{data['target']}' has no scaffold in "
                       f"templates/fileGen/fileGen.py::render. Either correct the "
                       f"fileType/ext pair in the project's fileGeneration.fileMap, "
                       f"or register the new file type by adding a case arm there "
                       f"(a context fileType also needs its --mode entry in "
                       f"pysrc/genFileParam.py::_CONTEXT_FILE_MODE).")
            exit(warningAndErrorReport())

# The two user slots every module interface unit scaffold seeds — the only two
# zones a hand-added dependency may legally occupy. Content in the wrong zone
# attaches to the wrong module and fails at link or cast time, not at the edit, so
# each label carries the rule it enforces. One wording serves every module unit
# (block, reg-handler, testbench top, testbench External).
# migrateModuleHeader._INSERT reproduces USER_IMPORTS_SLOT byte for byte so a
# restructured legacy file matches a fresh scaffold; change both together.
USER_INCLUDES_SLOT = (
    '// user #includes here (global module fragment - attaches to the global module)\n'
    '// Plain non-modular headers, including any whose definitions live in a .cpp.\n'
)
USER_IMPORTS_SLOT = (
    '// user imports here (module preamble - imports FIRST, then purview #includes)\n'
    '// A #include here closes the preamble and attaches to THIS module; use it only for\n'
    '// headers that name module or Config types.\n'
)

# C++20 module interface unit for a block's base class family (Base/Inverted/
# Channels). The `baseModuleHeader` scaffold owns the global module fragment and
# the `export module <block>.base;` declaration; the `baseClassDecl` region
# exports the class declarations. The file-level `--mode=module` routes
# baseClassDecl to its module-mode branch. Consumers `import <block>.base;`
# rather than textually including a header.
def blockBase_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --mode=module\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader\n')
    out.append('// GENERATED_CODE_END\n\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseClassDecl\n')
    out.append('\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))


# constructor etc for base class containing common architectureal definitions
def blockBase_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseConstructor --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=baseConstructor --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# header file for model implementation
def block_hdr(args, prj, data):
    out = list()
    blockUpper = data["block"].upper()
    out.append(f'#ifndef {blockUpper}_H\n')
    out.append(f'#define {blockUpper}_H\n\n')
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append('#include "systemc.h"\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=classDecl\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append(f'#endif //{blockUpper}_H\n')
    return("".join(out))

# cpp file for model implementation
def block_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# C++20 module interface unit for a parameterizable (hasOwnParams) block. The
# class declaration and all of its template member bodies live in one `.cppm`
# so a consumer registrar can `import <block>.block;` and instantiate
# `<block><Config>` with no out-of-line `.cpp`. The file-level `--mode=module`
# routes classDecl/constructor to their module-mode branches; the
# blockModuleHeader scaffold owns the global module fragment and the
# `export module <block>.block;` declaration.
def blockModule_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --mode=module\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_INCLUDES_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=moduleExport\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_IMPORTS_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=classDecl\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=constructor --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# C++20 module interface unit for a parameterizable (hasOwnParams) synthesized
# reg-handler block. Mirrors blockModule_cppm's moduleScaffold header wiring but
# routes the class body to the blockRegs sections (header/init/body) so the
# interface-forwarding hwRegisterIf<> members are emitted, not the plain
# hwRegister<> a normal block class carries. The file-level `--mode=module`
# routes the blockRegs sections to their module-mode branches; the
# blockModuleHeader scaffold owns the global module fragment and the
# `export module <block>.block;` declaration.
def blockRegsModule_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --mode=module\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_INCLUDES_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=moduleExport\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_IMPORTS_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=header\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# Per-block trampoline registrar module interface unit. The whole module
# (global module fragment #includes, `export module
# <project>.<parent>.<child>.registrar;`, the private `import <child>.block;`,
# and the anonymous-namespace trampoline static) is emitted by
# templates/systemc/blockRegistrar.py into the single generated region, mirroring
# how blockModule_cppm delegates its module body. The trampoline owns project-
# specific factory registration concerns for the block (parameterized SC lambdas
# with their per-Config tags). Pure non-templated SC-only blocks gain no
# trampoline (the cond predicate filters them out at file-generation time).
def blockRegistrar_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --parent={data["parent"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegistrar\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

# Per-assembler Verilated-wrapper registrar TU for a reused child. The whole body
# (the #ifdef VERILATOR guard, the reusable SC-wrapper + verilated DUT includes,
# the imported owner-qualified config module, and the anonymous-namespace `_verif`
# registration static) is emitted by templates/systemc/vlRegistrar.py (keyed off
# --parent) into the single generated region, mirroring blockRegistrar_cppm.
def blockVlRegistrar_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --parent={data["parent"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=vlRegistrar\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

# Owner-qualified foreign per-variant Config module interface unit for a reused
# child. The whole module body (global module fragment #includes, `export module
# <project>.<child>.config;`, and the exported per-variant Config structs) is
# emitted by templates/systemc/config.py (foreign mode, keyed off --parent) into
# the single generated region, mirroring how blockRegistrar_cppm delegates its
# module body. The file basename is owner-qualified
# (<project>_<child>VariantConfig.cppm).
def foreignConfig_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --parent={data["parent"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=config\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

# Parent-owned owner-qualified foreign per-variant SV verilated wrapper top for a
# reused child. The whole trampoline (the `include of the child's canonical .svh
# body and the owner-qualified top module binding the variant's resolved literals)
# is emitted by templates/systemVerilog/module_hdl_wrapper.py (foreign branch,
# keyed off --parent) into the single generated region. The file basename and the
# top module name are owner-qualified (<project>_<child>_<variant>_hdl_sv_wrapper).
def vlSvWrapForeign_sv(args, prj, data):
    guard = f'{data["headerName"].replace(".", "_").upper()}_GUARD_'
    out = list()
    out.append(f'`ifndef {guard}\n')
    out.append(f'`define {guard}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]} --parent={data["parent"]} --variant={data["variant"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper\n')
    out.append('// GENERATED_CODE_END\n\n')
    out.append(f'`endif // {guard}\n')
    return("".join(out))

def blockRegs_hdr(args, prj, data):
    out = list()
    blockUpper = data["block"].upper()
    out.append(f'#ifndef {blockUpper}_H\n')
    out.append(f'#define {blockUpper}_H\n\n')
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append('#include "systemc.h"\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=header\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // block implementation members\n\n')
    out.append('};\n\n')
    out.append(f'#endif //{blockUpper}_H\n')
    return("".join(out))

def blockRegs_src(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=blockRegs --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

# rtl file for implementation
def rtlModule(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances\n')
    out.append('// GENERATED_CODE_END\n')
    # The module begin-label is generator-owned and project-qualified; this
    # user-owned end-label must match it, so scaffold the qualified name.
    out.append(f'\nendmodule: {data["blockModuleName"]}\n')
    return("".join(out))

def rtlModuleRegs(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=moduleRegs\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

def rtlModuleApbDecode(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(f'// GENERATED_CODE_PARAM --block={data["block"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=apbDecodeModule\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

vlSvWrap_svTemplate = \
"""`ifndef ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_
`define ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper
// GENERATED_CODE_END

`endif // ___MODULENAME___HDL_SV_WRAPPER_SV_GUARD_
"""

# Variant trampoline top. The module_hdl_sv_wrapper template renders both the
# `include of the canonical parameterized body (the .svh) and the trampoline
# module into the generated region.
vlSvWrap_svVariantTemplate = \
"""`ifndef ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_
`define ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=__modulename__ --variant=__variantname__
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper
// GENERATED_CODE_END

`endif // ___MODULENAME_____VARIANTNAME___HDL_SV_WRAPPER_SV_GUARD_
"""

def vlSvWrap_sv(args, prj, data):
    if data['variant']:
        t = TemplateCustom(vlSvWrap_svVariantTemplate)
        return(t.substitute({'MODULENAME':data["block"].upper(), 'modulename':data["block"], 'VARIANTNAME':data['variant'].upper(), 'variantname':data['variant']}))
    else:
        t = TemplateCustom(vlSvWrap_svTemplate)
        return(t.substitute({'MODULENAME':data["block"].upper(), 'modulename':data["block"]}))

# Canonical parameterized SV wrapper body, emitted as an include-only .svh
# header. It keeps its GENERATED_CODE markers and is maintained by the
# generation scan, but is never Verilated as a top (a default-less parameterized
# module cannot be a top); the a2c-vl-wrap.mk top list filters to .sv only.
vlSvWrapBody_svhTemplate = \
"""`ifndef ___MODULENAME___HDL_SV_WRAPPER_SVH_GUARD_
`define ___MODULENAME___HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body
// GENERATED_CODE_END

`endif // ___MODULENAME___HDL_SV_WRAPPER_SVH_GUARD_
"""

def vlSvWrapBody_svh(args, prj, data):
    t = TemplateCustom(vlSvWrapBody_svhTemplate)
    return(t.substitute({'MODULENAME':data["block"].upper(), 'modulename':data["block"]}))

# The Verilated SC wrapper scaffold seeds the include guard, the create-only
# `GENERATED_CODE_PARAM` line, the generated-region markers, the user's
# `end_ctor_init` hook and the class's closing `};`. Everything the generator
# owns - the SystemC baseline, the `import <block>.base;` reference and the DUT
# SV-wrapper include - is emitted into the `preamble` generated region so
# `make gen` re-emits it every run and existing wrappers self-heal (e.g. after
# the Base header->C++20-module migration).
vlScWrap_hdrTemplate = \
"""#ifndef {{MODULENAME}}_HDL_SC_WRAPPER_H_
#define {{MODULENAME}}_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block={{modulename}}
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class
// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // {{MODULENAME}}_HDL_SC_WRAPPER_H_
"""

def vlScWrap_hdr(args, prj, data):
    t = J2Template(vlScWrap_hdrTemplate)
    return(t.render({'MODULENAME':data["block"].upper(), 'modulename':data["block"], 'variants':data['variants']})+'\n')

tandem_hdrTemplate = \
"""#ifndef __MODULENAME___TANDEM_H
#define __MODULENAME___TANDEM_H
// __copyright__

// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tandem --section=tandem
// GENERATED_CODE_END
private:
    // tandem implementation members
};

#endif //__MODULENAME___TANDEM_H
"""

def tandem_hdr(args, prj, data):
    t = TemplateCustom(tandem_hdrTemplate)
    return(t.substitute({'MODULENAME':data["block"].upper(),
                         'modulename':data["block"],
                         'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

tandem_srcTemplate = \
"""// __copyright__
// GENERATED_CODE_PARAM --block=__modulename__
// GENERATED_CODE_BEGIN --template=tandemConstructor --section=initTandem

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tandemConstructor --section=bodyTandem
// GENERATED_CODE_END
}
"""

def tandem_src(args, prj, data):
    t = TemplateCustom(tandem_srcTemplate)
    return(t.substitute({'modulename':data["block"],
                         'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

# Plain translation unit for the testbench Config class. Unlike the rest of the
# testbench family this is NOT a module unit, so it has no zone rules: the single
# user slot accepts `#include` and `import` interleaved in any order. Everything
# the class needs to compile - the framework prerequisite includes, the class
# declaration and the factory registration definition - lives in a generated
# region, so `make gen` can still revise the mechanism in an existing project.
# The scaffold owns only the overridable bodies between the class and registration
# regions.
tbConfigTemplate = \
"""// __copyright__

// GENERATED_CODE_PARAM --block=__modulename____variantparam__
// GENERATED_CODE_BEGIN --template=tbConfig --section=prerequisites
// GENERATED_CODE_END
// user #includes and imports here
// A plain translation unit, not a module: either may appear here in any order.
// GENERATED_CODE_BEGIN --template=tbConfig --section=class
// GENERATED_CODE_END

    bool createTestBench(void) override
    {
        // The testbench top self-registers; just call createTbTop().
        std::shared_ptr<blockBase> tb = createTbTop();
        return true;
    }

    void final(void) override
    {
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
// GENERATED_CODE_BEGIN --template=tbConfig --section=registration
// GENERATED_CODE_END
"""

# The `--variant` generated-code parameter, empty when the block declares none.
# Consumed downstream only by the templates that select the DUT Config and the
# factory variant string.
def _tb_variant_param(data):
    variant = data["variant"]
    return f" --variant={variant}" if variant else ""

def _tb_subst(data):
    # Substitution map for the tbConfig skeleton. There is exactly one testbench
    # artifact and class family per block, so `__tbclassname__` is always the plain
    # block name regardless of whether a `--variant` was supplied.
    subst = {
        'modulename':   data["block"],
        'tbclassname':  data["block"],
        'variantparam': _tb_variant_param(data),
        'copyright':    data["fileGeneration"]["fileCopyrightStatement"],
    }
    return subst

def tbConfig(args, prj, data):
    subst = _tb_subst(data)
    t = TemplateCustom(tbConfigTemplate)
    return(t.substitute(subst))

# The GENERATED_CODE_PARAM line of a testbench-family module unit. `--mode=module`
# routes the testbench templates to their module-mode branches. `--block` seeds the
# DUT; a user may retarget the External's at the `_tb` container and add
# `--excludeInst=<dut>`, so a template must resolve module identity from the
# parameters it is handed at gen time rather than from this seeded line.
def _tb_param_line(data):
    return f'// GENERATED_CODE_PARAM --block={data["block"]}{_tb_variant_param(data)} --mode=module\n'

# C++20 module interface unit for a block's testbench top. Wholly generated apart
# from the copyright and the two user slots: the testbench section=header region
# owns the whole class including its closing `};`, so the scaffold owns no class
# seam. The slots are still seeded so a scoreboard header or an import has a legal
# zone to go in.
def testBench_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(_tb_param_line(data))
    out.append('// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_INCLUDES_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_IMPORTS_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=testbench --section=header\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=testbench --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))

# C++20 module interface unit for a block's testbench External (the inverted
# stimulus/checker peer of the DUT). Follows the blockModule_cppm seam pattern: the
# scaffold owns the closing `};` of both the class and the constructor body, so the
# user keeps an in-class member slot and an in-constructor-body slot.
def tbExternal_cppm(args, prj, data):
    out = list()
    out.append(f'//{data["fileGeneration"]["fileCopyrightStatement"]}\n\n')
    out.append(_tb_param_line(data))
    out.append('// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_INCLUDES_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal\n')
    out.append('// GENERATED_CODE_END\n')
    out.append(USER_IMPORTS_SLOT)
    out.append('// GENERATED_CODE_BEGIN --template=tbExternal --section=header\n')
    out.append('\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('    // external implementation members\n\n')
    out.append('};\n\n')
    out.append('// GENERATED_CODE_BEGIN --template=tbExternal --section=init\n')
    out.append('// GENERATED_CODE_END\n')
    out.append('// GENERATED_CODE_BEGIN --template=tbExternal --section=body\n')
    out.append('    // GENERATED_CODE_END\n')
    out.append('};\n\n')
    return("".join(out))

include_cppmTemplate = \
"""
// GENERATED_CODE_PARAM __paramtail__
// __copyright__

// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=headers
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsHeader
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=testStructsCPP
// GENERATED_CODE_END
"""

config_hdrTemplate = \
"""
#ifndef __HEADERGUARD___
#define __HEADERGUARD___
// __copyright__

// GENERATED_CODE_PARAM __paramtail__
// GENERATED_CODE_BEGIN --template=config
// GENERATED_CODE_END

#endif //__HEADERGUARD___
"""

def include_cppm(args, prj, data):
    t = TemplateCustom(include_cppmTemplate)
    return(t.substitute({
        'paramtail':contextParamTail(data["project"], data["context"],
                                    contextParamMode(data["target"])),
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

def config_hdr(args, prj, data):
    t = TemplateCustom(config_hdrTemplate)
    return(t.substitute({
        'HEADERGUARD':data["headerName"].replace('.', '_').upper(),
        'paramtail':contextParamTail(data["project"], data["context"],
                                    contextParamMode(data["target"])),
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

includeFW_hdrTemplate = \
"""
#ifndef __HEADERGUARD___
#define __HEADERGUARD___
// __copyright__

// GENERATED_CODE_PARAM __paramtail__
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// GENERATED_CODE_END
#endif //__HEADERGUARD___
"""
def includeFW_hdr(args, prj, data):
    t = TemplateCustom(includeFW_hdrTemplate)
    return(t.substitute({
        'HEADERGUARD':data["headerName"].replace('.', '_').upper(),
        'paramtail':contextParamTail(data["project"], data["context"],
                                    contextParamMode(data["target"])),
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

# Structurally empty today - codeMapping['fw'] declares no 'split' feature, so both
# regions render nothing but their markers. The file is kept as reserved headroom:
# adding a split fw feature makes it carry out-of-line definitions with no scaffold
# change, because the cppIncludes region already owns the whole preamble (the paired
# header include and the fw `using`).
includeFW_srcTemplate = \
"""
// __copyright__
// GENERATED_CODE_PARAM __paramtail__
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp --namespace=__fwnamespace__
// GENERATED_CODE_END
"""
def includeFW_src(args, prj, data):
    t = TemplateCustom(includeFW_srcTemplate)
    return(t.substitute({
        'fwnamespace':FW_NAMESPACE,
        'paramtail':contextParamTail(data["project"], data["context"],
                                    contextParamMode(data["target"])),
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

package_svTemplate = \
"""
// __copyright__
// GENERATED_CODE_PARAM __paramtail__
// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv
// GENERATED_CODE_END
"""
def package_sv(args, prj, data):
    t = TemplateCustom(package_svTemplate)
    return(t.substitute({
        'paramtail':contextParamTail(data["project"], data["context"],
                                    contextParamMode(data["target"])),
        'copyright':data["fileGeneration"]["fileCopyrightStatement"]}))

# Per-project verilator file list (rtl.f). The +libext line and the
# owning-project GENERATED_CODE_PARAM are the create-only skeleton; the rtlDotF
# template fills the generated region with the +incdir lines and the ordered
# package list for every context on the top context's include chain. The
# --project stamp names the owning project directly, so owner resolution needs no
# context/basename round-trip.
def rtlDotF_f(args, prj, data):
    out = list()
    out.append('+libext+.sv\n')
    out.append(f'// GENERATED_CODE_PARAM --project={data["project"]}\n')
    out.append('// GENERATED_CODE_BEGIN --template=rtlDotF\n')
    out.append('// GENERATED_CODE_END\n')
    return("".join(out))
