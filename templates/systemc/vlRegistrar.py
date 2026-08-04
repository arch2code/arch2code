# Per-block Verilated-wrapper registrar template.
#
# Emits the body of a generated `<child>VlRegistrar.cpp` translation unit: the
# `_verif` factory registrations for a reused child's Verilated SystemC wrapper,
# one per (assembler, child) instance edge. This is the verilated counterpart of
# blockRegistrar.py (which owns the `_model` registrations). The wrapper-local
# `struct registerBlock` / `static registerBlock_` mechanism and the old
# `vl_wrap.cpp` aggregator it fed are superseded by this per-assembler TU.
#
# The whole TU is guarded by `#ifdef VERILATOR`: outside a verilated build it is
# empty. It is an ordinary (non-module) registration TU discovered as a
# registrar/ source, so it #includes the reusable `<child>_hdl_sc_wrapper.h`
# template and the verilated `V<top>.h` DUT header(s), and — critically — imports
# the SAME owner-qualified config module the container and SC registrar import,
# so the container's `dynamic_pointer_cast<<child>Base<Config>>` is non-null: the
# registered wrapper is built on that exact Config type.

import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.intf_gen_utils import sc_concrete_dut
from pysrc.arch2codeHelper import printError, warningAndErrorReport


def render(args, prj, data):
    out = list()
    blockName = data['blockName']
    qualBlock = data['qualBlock']
    isParameterizable = data['isParameterizable']
    hasOwnParams = data['hasOwnParams']
    defaultConfig = data['defaultConfig'] if isParameterizable else ''
    sv = data['svWrapper']

    parentBlock = data.get('parent')
    if not parentBlock:
        printError(f"vlRegistrar: block '{blockName}' has no --parent on its "
                   f"GENERATED_CODE_PARAM line; re-run `make newmodule` (registrar "
                   f"mode) to rescaffold the VlRegistrar .cpp files.")
        exit(warningAndErrorReport())

    registrarConfig = prj.getRegistrarConfigView(qualBlock, parentBlock)
    variantDescriptors = registrarConfig['variantDescriptors']
    variants = sorted(data['variants'].keys())

    # projectName the `_verif` key is registered under: the same projectName the
    # container's createInstance lookup targets (mirrors createInstanceProjectName
    # / getBDInstances). A parameterizable child re-registers under the assembling
    # project; a plain child owned by another project registers under its owner.
    assemblerProject = prj.config.getConfig('PROJECTNAME')
    childOwner = prj.contextOwningProject[data['blockInfo']['_context']]
    keyProject = assemblerProject if isParameterizable else childOwner

    # Per-variant Verilated DUT class + header: a variant the assembler declares
    # foreign to the reused child binds the owner-qualified SV top; a same-project
    # variant binds the bare child-emitted top.
    def dutClass(variant):
        desc = variantDescriptors.get(variant)
        if desc is not None and desc['isForeign']:
            return sv['foreignVariantDutClasses'][variant]
        return sv['variantDutClasses'][variant]

    def dutHeader(variant):
        desc = variantDescriptors.get(variant)
        if desc is not None and desc['isForeign']:
            return sv['foreignVariantDutHeaders'][variant]
        return sv['variantDutHeaders'][variant]

    out.append('#ifdef VERILATOR')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')
    out.append(f'#include "{sv["scWrapperInclude"]}"')

    # Verilated DUT header(s): one per variant, or the block's single body header
    # for a wrapper with no instance-bound variants. First occurrence preserved.
    dutHeaders = [dutHeader(v) for v in variants] if variants else [sc_concrete_dut(sv, data['declaredVariants'])['dutHeader']]
    seenHdr = set()
    for hdr in dutHeaders:
        if hdr in seenHdr:
            continue
        seenHdr.add(hdr)
        out.append(f'#include "{hdr}"')

    # Same-project Config-policy header(s) for the concrete Config types the
    # parameterized lambda spells (the block view owns this selection).
    for context in sorted(data.get('configIncludeContext', {})):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')

    # Owner-qualified foreign-Config modules for variants the assembler declares
    # foreign to the reused child; imported (not #included) so the lambda body
    # spells the owner-qualified Config type on the SAME module the container
    # imports, keeping the container's dynamic_pointer_cast non-null.
    for mod in registrarConfig['foreignConfigModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    out.append('')
    out.append(f'namespace {{')
    out.append(f'struct _{blockName}_vl_registrar {{')
    out.append(f'    _{blockName}_vl_registrar() {{')

    scWrapper = sv['scWrapperModule']
    if variants:
        for variant in variants:
            if hasOwnParams:
                desc = variantDescriptors.get(variant)
                perVariantConfig = intf_gen_utils.cpp_descriptor_config_name(desc, defaultConfig) \
                    if desc else defaultConfig
                target = f'{scWrapper}<{dutClass(variant)}, {perVariantConfig}>'
            else:
                target = f'{scWrapper}<{dutClass(variant)}>'
            out.extend(_emit_register_call(
                blockName=blockName, targetClass=target, variant=variant,
                projectName=keyProject, indent='        '))
    else:
        out.extend(_emit_register_call(
            blockName=blockName, targetClass=scWrapper, variant='',
            projectName=keyProject, indent='        '))

    out.append('    }')
    out.append('};')
    out.append(f'static _{blockName}_vl_registrar _{blockName}_vl_registrar_instance;')
    out.append(f'}} // namespace')
    out.append('#endif // VERILATOR')
    return '\n'.join(out)


def _emit_register_call(*, blockName, targetClass, variant, projectName, indent):
    # A single instanceFactory::registerBlock(...) for the `_verif` verilated
    # wrapper. The factory key is (blockType, variant, projectName): the `_verif`
    # suffix is the verification-wrapper registration token (mirrors the `_model`
    # token blockRegistrar uses), the variant string selects the per-variant
    # Config policy, and projectName matches the container's createInstance lookup.
    return [
        f'{indent}instanceFactory::registerBlock(',
        f'{indent}    "{blockName}_verif",',
        f'{indent}    [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{',
        f'{indent}        return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{targetClass}>(blockName, variant, bbMode));',
        f'{indent}    }},',
        f'{indent}    "{variant}", "{projectName}");',
    ]
