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

    # Per-variant Config descriptors. Each descriptor names the Config struct
    # the lambda's templated block class instantiates against; when the
    # descriptor's resolved values are empty, we fall back to the default Config
    # name so the generated shape continues to link.
    variantConfigName = dict()
    for desc in data['variantConfigs']:
        if desc['values']:
            variantConfigName[desc['variant']] = desc['configName']
        else:
            variantConfigName[desc['variant']] = defaultConfig

    out.append('#include "instanceFactory.h"')
    out.append('#include "blockBase.h"')

    # Per-context Config-policy headers must be reachable for the
    # parameterized lambda body. The block view owns this selection.
    for context in sorted(data.get('configIncludeContext', {})):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')

    # Block class header. Pulled in unconditionally for the
    # parameterized-block branch so the lambda can construct
    # `<B><Config>`.
    if isParameterizable:
        out.append(f'#include "{blockName}.h"')

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
            perVariantConfig = variantConfigName.get(variant, defaultConfig)
            return f'{blockName}<{perVariantConfig}>'

        if variants:
            for variant in variants:
                out.extend(_emit_register_call(
                    suffix='model',
                    blockName=blockName,
                    targetClass=_target(variant),
                    variant=variant,
                    indent='        ',
                ))
        else:
            out.extend(_emit_register_call(
                suffix='model',
                blockName=blockName,
                targetClass=_target(''),
                variant='',
                indent='        ',
            ))

    out.append('    }')
    out.append('};')
    out.append(f'static _{blockName}_registrar _{blockName}_registrar_instance;')
    out.append(f'}} // namespace')
    return '\n'.join(out)


def _emit_register_call(*, suffix, blockName, targetClass, variant, indent):
    """Emit a single instanceFactory::registerBlock(...) call.

    Under variant ≅ Config the factory key is `(blockType, variant)`;
    the variant string identifies the per-variant Config policy
    unambiguously.
    """
    return [
        f'{indent}instanceFactory::registerBlock(',
        f'{indent}    "{blockName}_{suffix}",',
        f'{indent}    [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{',
        f'{indent}        return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{targetClass}>(blockName, variant, bbMode));',
        f'{indent}    }},',
        f'{indent}    "{variant}");',
    ]
