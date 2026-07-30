# Per-block trampoline registrar template.
#
# Emits the body of a generated `<block>Registrar.cpp` translation unit.
# The trampoline is the single TU per (block, project) that owns every
# project-specific factory registration concern for the block:
#
#   * SystemC parameterized-block registrations, one lambda per
#     (blockType, variant) pair the project's instance tree binds.
#     The variant string identifies the per-variant Config policy
#     unambiguously; the trampoline lambda constructs
#     `make_shared<B<<perVariantConfig>>>` directly.
#   * Verilated wrapper registrations under the `_verif` suffix when the
#     block has `hasVl: true`. The wrapper-local
#     `struct registerBlock` / `static registerBlock_` mechanism is
#     superseded.
#
# The trampoline no longer emits `instanceFactory::addParam(...)`. Block
# constructors now read parameter values from `Config::*` directly, and the
# runtime addParam / getParam table on instanceFactory is decommissioned.
#
# Pure non-templated SC-only blocks reach the factory through the
# self-registering static emitted in their own `<block>.cpp` and do not
# need a trampoline — `cond: {isParameterizable: true, hasVl: true}` filters
# them out at file-generation time.
#
# The trampoline TU must be linked unconditionally into the program; the
# linker-strip hazard that the active force-link function solves for
# non-templated self-registering blocks does not apply here because the
# trampoline is referenced directly.
#
# The current implementation uses the block's default Config policy as the only
# binding for cases that do not have per-instance Config propagation.

import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, warningAndErrorReport

def render(args, prj, data):
    return render_default(args, prj, data)


def render_default(args, prj, data):
    out = list()
    blockName = data['blockName']
    qualBlock = data['qualBlock']
    blockInfo = data['blockInfo']
    isParameterizable = data['isParameterizable']
    # Only leaf parameterizable blocks (those with their own `params:`) are
    # class templates. Non-leaf containers flagged isParameterizable solely
    # because parameterizable structures transit their surface remain
    # non-templated and must NOT receive a `<Config>` template argument in the
    # trampoline's `make_shared` call.
    hasOwnParams = data['hasOwnParams']
    defaultConfig = data['defaultConfig'] if isParameterizable else ''

    # The variant set is the project's instance-bound variant set for
    # this block. `data['variants']` is populated by getBDInstances and
    # already reflects only variants that the project's instance tree
    # actually selects, so there is no separate filter needed here.
    variants = sorted(data['variants'].keys())

    # Per-variant Config selection resolved against the parent's owning project:
    # the trampoline binds the same Config the parent's own instances bind, so a
    # variant the parent declares as a foreign (assembler-owned) variant of the
    # reused child gets the owner-qualified struct. The view also supplies the
    # foreign registrar-domain headers this TU must include.
    parentBlock = data.get('parent')
    if not parentBlock:
        printError(f"blockRegistrar: block '{blockName}' has no --parent on its "
                   f"GENERATED_CODE_PARAM line; re-run `make newmodule` (registrar "
                   f"mode) to rescaffold the registrar .cppm files.")
        exit(warningAndErrorReport())
    registrarConfig = prj.getRegistrarConfigView(qualBlock, parentBlock)
    variantDescriptors = registrarConfig['variantDescriptors']

    # The registrar is a C++20 module interface unit whose module name is
    # parent-qualified (`<project>.<parent>.<child>.registrar`), so the same
    # child reused under two parents yields two distinct registrar modules that
    # coexist in one binary. The parent identity rides on the param line
    # (systemcGen threads `--parent` into data['parent']).
    projectName = prj.config.getConfig('PROJECTNAME')
    registrarModule = intf_gen_utils.cpp_registrar_module_name(projectName, parentBlock, blockName)

    # Global module fragment. Config stays sourced from the leaf-context header
    # (config-policy header(s) below), so every config type remains
    # header-attached and consistent across container/verif/TB. #includes are
    # illegal in module purview, so all textual headers live here in the GMF.
    out.append('module;')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')

    # Per-context Config-policy headers must be reachable for the
    # parameterized lambda body. The block view owns this selection.
    for context in sorted(data.get('configIncludeContext', {})):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')

    # A non-templated container flagged isParameterizable is still a classic
    # header class; its declaration must be visible in the GMF because includes
    # are illegal after the module declaration.
    if isParameterizable and not hasOwnParams:
        out.append(f'#include "{blockName}.h"')

    out.append('')
    out.append(f'export module {registrarModule};')

    # Block class visibility for the parameterized-block lambda so it can
    # construct `<B><Config>`. A hasOwnParams block lives in its own C++20
    # module interface unit (`<block>.cppm`), so the trampoline imports it as a
    # PRIVATE import (plain `import`, not `export import`): the registrar exports
    # nothing, it only runs its trampoline static.
    if isParameterizable and hasOwnParams:
        out.append(f'import {intf_gen_utils.cpp_block_module_name(data["blockModuleName"])};')

    # Owner-qualified foreign-Config modules for variants the parent declares as
    # foreign variants of the reused child; the lambda body spells those owner-
    # qualified Config types. Imported as PRIVATE imports (plain `import`) in the
    # registrar's module purview, after `export module`, not as GMF #includes.
    for mod in registrarConfig['foreignConfigModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    # NOTE: Verilated wrapper registration is intentionally NOT emitted
    # here yet. The wrapper header (`<block>_hdl_sc_wrapper.h`) lives
    # in `verif/vl_wrap/` and is only on the include path under
    # `VL_DUT=1`. Today's `templates/systemc/module_hdl_wrapper.py`
    # together with `verif/vl_wrap/vl_wrap.cpp` already register the
    # `_verif` suffix entries through the wrapper-local
    # `struct registerBlock` / explicit-specialization pattern. The
    # plan's verilated-wrapper migration moves that registration into
    # a per-block trampoline that lives alongside `vl_wrap.cpp` in
    # `verif/vl_wrap/`; that migration is a separate iteration. Until
    # then this trampoline emits SC parameterized-block registrations
    # only and the cond predicate is restricted to `isParameterizable: true`
    # so non-templated `hasVl` blocks gain no (empty) trampoline.

    out.append('')
    out.append(f'namespace {{')
    out.append(f'struct _{blockName}_registrar {{')
    out.append(f'    _{blockName}_registrar() {{')

    # SC-model registrations for parameterized blocks. Emit one entry
    # per (blockType, variant) pair. The per-variant Config struct name comes
    # from the descriptor list when one is available; the variant string is the
    # factory key. Non-leaf
    # parameterizable blocks (hasOwnParams=False) are non-templated, so
    # `make_shared<B>` rather than `make_shared<B<Config>>` is emitted.
    if isParameterizable:
        def _target(variant):
            if not hasOwnParams:
                return blockName
            desc = variantDescriptors.get(variant)
            perVariantConfig = intf_gen_utils.cpp_descriptor_config_name(desc, defaultConfig) if desc else defaultConfig
            return f'{blockName}<{perVariantConfig}>'

        if variants:
            for variant in variants:
                out.extend(_emit_register_call(
                    suffix='model',
                    blockName=blockName,
                    targetClass=_target(variant),
                    variant=variant,
                    projectName=projectName,
                    indent='        ',
                ))
        else:
            out.extend(_emit_register_call(
                suffix='model',
                blockName=blockName,
                targetClass=_target(''),
                variant='',
                projectName=projectName,
                indent='        ',
            ))

    out.append('    }')
    out.append('};')
    out.append(f'static _{blockName}_registrar _{blockName}_registrar_instance;')
    out.append(f'}} // namespace')
    return '\n'.join(out)


def _emit_register_call(*, suffix, blockName, targetClass, variant, projectName, indent):
    """Emit a single instanceFactory::registerBlock(...) call.

    The factory key is `(blockType, variant, projectName)`; the variant
    string identifies the per-variant Config policy unambiguously within a
    project and projectName is the assembling project's projectName so the
    container's projectName-qualified createInstance lookup matches this
    registration.
    """
    return [
        f'{indent}instanceFactory::registerBlock(',
        f'{indent}    "{blockName}_{suffix}",',
        f'{indent}    [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{',
        f'{indent}        return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{targetClass}>(blockName, variant, bbMode));',
        f'{indent}    }},',
        f'{indent}    "{variant}", "{projectName}");',
    ]
