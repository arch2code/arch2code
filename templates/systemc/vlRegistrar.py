# Per-block HDL-wrapper registrar template: the `_verif` factory registrations of
# a reused child's `<child>_hdl_sc_wrapper`, one TU per child aggregating every
# parent-child factory domain. Empty unless an HDL DUT build (VERILATOR, VCS_DUT
# or XCELIUM_DUT) is selected; the DUT class per top is `V<top>` (Verilator), the
# vlogan shell `<top>` (VCS) or the foreign-module shell `<top>` (Xcelium), hidden
# behind a `<top>_dut_t` alias so the registrations are spelled once. The config
# module import must be the one the container imports, or the container's
# `dynamic_pointer_cast<<child>Base<Config>>` sees mismatched RTTI.

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
    out.append('#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)')
    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')
    out.append(f'#include "{sv["scWrapperInclude"]}"')

    # One DUT header per distinct top, in the simulator's spelling.
    tops = list(dict.fromkeys(reg['topModule'] for reg in verifRegistrations))
    byTop = {reg['topModule']: reg for reg in verifRegistrations}
    out.append('#if defined(VERILATOR)')
    for top in tops:
        out.append(f'#include "{byTop[top]["dutHeader"]}"')
    out.append('#elif defined(VCS_DUT)')
    for top in tops:
        out.append(f'#include "{byTop[top]["vcsDutHeader"]}"')
    out.append('#else')
    for top in tops:
        out.append(f'#include "{byTop[top]["xceliumDutHeader"]}"')
    out.append('#endif')

    # Imported from the same module the container imports; a second declaration
    # would give the container's dynamic_pointer_cast mismatched RTTI.
    for mod in registrarConfig['verifConfigModules']:
        out.append(f'import {intf_gen_utils.cpp_config_module_name(mod["project"], mod["block"])};')

    out.append('')
    out.append(f'namespace {{')
    out.append('#if defined(VERILATOR)')
    for top in tops:
        out.append(f'using {top}_dut_t = {byTop[top]["dutClass"]};')
    out.append('#elif defined(VCS_DUT)')
    for top in tops:
        out.append(f'using {top}_dut_t = {byTop[top]["vcsDutClass"]};')
    out.append('#else')
    for top in tops:
        out.append(f'using {top}_dut_t = {byTop[top]["xceliumDutClass"]};')
    out.append('#endif')
    # The boundary files bind each payload pin to a width evaluated at database
    # creation; the SC wrapper sizes the same pin from the Config's structure.
    if sv['scWrapperConfigTemplated']:
        for top in tops:
            config = intf_gen_utils.cpp_config_expression_name(byTop[top]['config'])
            for pin in prj.getVlTopBoundaryPins(data, top):
                if not pin['structureKey']:
                    continue
                structType = intf_gen_utils.sc_struct_type_name(
                    pin['structure'], pin['structureKey'], prj, config_override=config)
                out.append(f'static_assert({structType}::_bitWidth == {pin["width"]}, '
                           f'"{top}: {pin["pin"]} width differs from the generated boundary");')
    out.append(f'struct _{blockName}_vl_registrar {{')
    out.append(f'    _{blockName}_vl_registrar() {{')

    # A block reaching a per-variant registration always emits its wrapper as a
    # class template, since having a variant at all requires declared params.
    scWrapper = sv['scWrapperModule']
    for reg in verifRegistrations:
        perVariantConfig = intf_gen_utils.cpp_config_expression_name(reg['config']) \
            if reg['config'] is not None else ''
        targetClass = f'{scWrapper}<{reg["topModule"]}_dut_t, {perVariantConfig}>' \
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
    out.append('#endif // VERILATOR || VCS_DUT || XCELIUM_DUT')
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
