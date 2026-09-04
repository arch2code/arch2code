# Per-block Verilated-wrapper registrar template.
#
# Emits the body of a generated `<child>VlRegistrar.cpp`: the `_verif` factory
# registrations for a reused child's Verilated SystemC wrapper. One child-named
# TU aggregates all parent-child factory domains in the project.
#
# The whole TU is guarded by `#ifdef VERILATOR`, so outside a verilated build it
# is empty. It is an ordinary (non-module) registration TU discovered as a
# registrar/ source, so it #includes the reusable `<child>_hdl_sc_wrapper.h`
# template and the verilated `V<top>.h` DUT headers. It imports the same
# owner-qualified config module the container and SC registrar import, so the
# container's `dynamic_pointer_cast<<child>Base<Config>>` finds a wrapper built
# on that exact Config type.

import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, warningAndErrorReport


def render(args, prj, data):
    out = list()
    blockName = data['blockName']
    qualBlock = data['qualBlock']
    sv = data['svWrapper']

    parentBlock = data.get('parent')
    if not parentBlock:
        printError(f"vlRegistrar: block '{blockName}' has no --parent on its "
                   f"GENERATED_CODE_PARAM line; re-run `make newmodule` (registrar "
                   f"mode) to rescaffold the VlRegistrar .cpp files.")
        exit(warningAndErrorReport())

    registrarConfig = prj.getRegistrarConfigView(qualBlock, parentBlock)
    # One entry per variant a site can ask this child for, each carrying the
    # Config its wrapper is built at. For a child reached only through
    # inheritContainerParam these are the CONTAINER's variants.
    verifRegistrations = registrarConfig['verifRegistrations']

    # projectName the `_verif` key is registered under: the same projectName the
    # container's createInstance lookup targets (mirrors createInstanceProjectName
    # / getBDInstances). A child that owns params re-registers under the assembling
    # project; a child owned by another project but only transiting parameterized
    # types registers under its owner.
    childOwner = prj.contextOwningProject[data['blockInfo']['_context']]
    out.append('#ifdef VERILATOR')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')
    out.append(f'#include "{sv["scWrapperInclude"]}"')

    # Verilated DUT header(s): one per persisted concrete registration.
    dutHeaders = [reg['dutHeader'] for reg in verifRegistrations]
    seenHdr = set()
    for hdr in dutHeaders:
        if hdr in seenHdr:
            continue
        seenHdr.add(hdr)
        out.append(f'#include "{hdr}"')

    # Same-project Config-policy header(s) for the concrete Config types the
    # parameterized lambda spells (the block view owns this selection).
    configContexts = set(data['configIncludeContext']) \
        | set(registrarConfig['configHeaderContexts'])
    for context in sorted(configContexts):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')

    # Owner-qualified foreign-Config modules for the variants registered below;
    # imported (not #included) so the lambda body spells the owner-qualified
    # Config type on the SAME module the container imports, keeping the
    # container's dynamic_pointer_cast non-null.
    for mod in registrarConfig['verifForeignConfigModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    out.append('')
    out.append(f'namespace {{')
    out.append(f'struct _{blockName}_vl_registrar {{')
    out.append(f'    _{blockName}_vl_registrar() {{')

    # A block reaching a per-variant registration always emits its wrapper as a
    # class template, since having a variant at all requires declared params.
    scWrapper = sv['scWrapperModule']
    for reg in verifRegistrations:
        perVariantConfig = intf_gen_utils.cpp_config_expression_name(reg['config']) \
            if reg['config'] is not None else ''
        targetClass = f'{scWrapper}<{reg["dutClass"]}, {perVariantConfig}>' \
            if sv['scWrapperConfigTemplated'] else scWrapper
        out.extend(_emit_register_call(
            blockName=blockName,
            targetClass=targetClass,
            variant=reg['variant'],
            projectName=reg['factoryProject'] if data['hasOwnParams'] else childOwner,
            indent='        '))

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
