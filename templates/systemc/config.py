import pysrc.emissionUtils as emissionUtils
from pysrc.intf_gen_utils import cpp_variant_config_name, cpp_config_module_name

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # A registrar-domain foreign-Config header carries a --parent on its param
    # line (block+parent mode); the context-mode default/same-project header does
    # not. Foreign mode emits only the owner-qualified assembler-declared structs.
    if 'parent' in data:
        return(foreignConfig(args, prj, data))
    return(includeConfig(args, prj, data))


def foreignConfig(args, prj, data):
    # Owner-qualified per-variant Config structs for the reused child block
    # `data['qualBlock']`, declared foreign by the parent `data['parent']`'s
    # owning project, emitted as a C++20 module interface unit. Member layout
    # mirrors the child's context config header (base parameterizable members
    # plus eval-derived members emitted symbolically); only the struct name is
    # owner-qualified. The whole module (global module fragment #includes,
    # `export module <project>.<child>.config;`, and the exported structs) is
    # emitted here into the scaffold's single generated region, so a consumer
    # container/registrar imports the module rather than including a header.
    view = prj.getForeignConfigData(data['qualBlock'], data['parent'])
    descriptors = view['descriptors']
    if not descriptors:
        return ""
    params = view['params']
    constants_by_name = {value['constant']: value for value in params}
    block_param_synthetic = view['blockParamSynthetic']
    # One config module per (owning project, child); every descriptor here shares
    # that identity (getForeignConfigData filters to the owner project and one
    # child). The module name is spelled in the template layer from the neutral
    # (project, child) components.
    moduleName = cpp_config_module_name(descriptors[0]['declaringProject'],
                                        descriptors[0]['block'])
    out = []
    # #includes are illegal in module purview, so the config struct's constexpr
    # dependencies live in the global module fragment ahead of the module decl.
    out.append('module;')
    out.append('#include <cstdint>')
    out.append('#include "clog2.h"')
    out.append("")
    out.append(f'export module {moduleName};')
    out.append("")
    # getForeignConfigData yields only canonical descriptors (duplicateOf is
    # None) whose struct name is unique, so each struct is emitted exactly once.
    # The name is spelled here in the template layer from the descriptor's
    # neutral (project, block, variant) components. Each struct is exported so a
    # module consumer can name it unqualified, exactly as the header form did.
    for desc in descriptors:
        structName = cpp_variant_config_name(desc['declaringProject'], desc['block'],
                                             desc['emitVariant'], desc['isForeign'])
        out.append(f"export struct {structName} {{")
        variantSpelling = _configSymSpelling(prj, set(desc['values'].keys()))
        for constName, resolved in desc['values'].items():
            if constName in constants_by_name:
                constData = constants_by_name[constName]
                rhs = _configMemberRhs(constData, resolved, variantSpelling)
            else:
                constData = block_param_synthetic[constName]
                constData = dict(constData, value=resolved)
                rhs = resolved
            type_str = _config_type(constData)
            out.append(f"    static constexpr {type_str} {constName} = {rhs};")
        out.append("};")
        out.append("")
    return("\n".join(out))


def emitCStyleCanonical(evalCanonical, symSpelling):
    """Translate a persisted canonical eval expression into a C/C++ expression
    string suitable for the RHS of a constexpr or firmware-header initializer
    (see emissionUtils.emitExpr)."""
    return emissionUtils.emitExpr(evalCanonical, symSpelling, emissionUtils.C)


def configStructLines(prj, data, structName, baseValues):
    """Emit the lines for one Config struct given base-value overrides.

    baseValues: {base-parameterizable-constant-name: int}. Base parameterizable
    members emit the supplied override (or their declared value); eval-derived
    members emit symbolically through their canonical expression so each struct
    recomputes them from its own base members (see _configMemberRhs)."""
    params = [value for value in data['constants'].values() if value['isParameterizable']]
    spelling = _configSymSpelling(prj, {value['constant'] for value in params})
    out = [f"struct {structName} {{"]
    for value in params:
        type_str = _config_type(value)
        rhs = _configMemberRhs(value, baseValues.get(value['constant'], value['value']), spelling)
        out.append(f"    static constexpr {type_str} {value['constant']} = {rhs};")
    out.append("};")
    return out


def includeConfig(args, prj, data):
    out = []
    params = [value for value in data['constants'].values() if value['isParameterizable']]
    # Synthetic block-param fields (declared via `params:` with no backing
    # parameterizable constant) and per-variant Config descriptors are
    # supplied by getContextData(); the template performs no cross-block
    # walks.
    constants_by_name = {p['constant']: p for p in params}
    block_param_synthetic = data['contextBlockParamSynthetic']
    variant_entries = data['contextVariantConfigs']
    # The Config struct members are `static constexpr uint*_t`, so this region
    # owns <cstdint> for every context, including one with no parameterizable
    # constants at all - hence ahead of the paramless early return below, which
    # would otherwise leave such a header depending on the scaffold's copy.
    # Matches the foreignConfig module path, which emits it in its own region.
    out.append('#include <cstdint>')
    if not params and not block_param_synthetic and not variant_entries:
        return "\n".join(out)
    # Config structs may emit eval-derived members that use clog2; the
    # dedicated clog2 header supplies that constexpr helper unconditionally.
    out.append('#include "clog2.h"')
    out.append("")
    # Legacy per-context Config struct. Retained for blocks that still ride on
    # <context>DefaultConfig (those without their own variants but
    # parameterizable transitively).
    # Pure block params (block_param_synthetic) are intentionally NOT
    # emitted here: there is no constant default, so any caller reading
    # them through the legacy default fallback is a usage bug. Per-variant
    # Config structs (below) carry the override values.
    # The struct name must be the same identifier consumer blocks reference
    # as their Config type, i.e. blocks.defaultConfig. Mirror the exact
    # context-stem sanitization used by calcBlockConfigInfo() (both '-' and
    # '.' mapped to '_') so the emitted name never drifts from the persisted
    # one.
    configName = f"{data['contextStem'].replace('-', '_').replace('.', '_')}DefaultConfig"
    out.append(f"struct {configName} {{")
    defaultSpelling = _configSymSpelling(prj, {value['constant'] for value in params})
    for value in params:
        type_str = _config_type(value)
        rhs = _configMemberRhs(value, value['value'], defaultSpelling)
        out.append(f"    static constexpr {type_str} {value['constant']} = {rhs};")
    out.append("};")
    out.append("")
    # Per-variant Config structs. Variant labels and resolved values come
    # from the context view; intra-block dedup (duplicateOf) folds byte-
    # identical variants onto a single canonical struct.
    # Seed with the legacy context-stem default name: a block whose own
    # default-variant config resolves to `<contextStem>DefaultConfig` (block
    # name == YAML file stem) names the same struct already emitted above, so
    # re-emitting it would be a redefinition.
    seen_struct_names = {configName}
    for entry in variant_entries:
        desc = entry['descriptor']
        if desc['duplicateOf'] is not None:
            continue
        if not desc['values']:
            continue
        # Canonical, non-empty descriptor: spell its struct name in the template
        # layer from the neutral components.
        structName = cpp_variant_config_name(desc['declaringProject'], desc['block'],
                                             desc['emitVariant'], desc['isForeign'])
        if structName in seen_struct_names:
            continue
        seen_struct_names.add(structName)
        out.append(f"struct {structName} {{")
        variantSpelling = _configSymSpelling(prj, set(desc['values'].keys()))
        for constName, resolved in desc['values'].items():
            if constName in constants_by_name:
                constData = constants_by_name[constName]
                rhs = _configMemberRhs(constData, resolved, variantSpelling)
            else:
                # Synthetic block-param entry. Treated as an unsigned
                # 32-bit field; the variant override is the value source.
                constData = block_param_synthetic[constName]
                constData = dict(constData, value=resolved)
                rhs = resolved
            type_str = _config_type(constData)
            out.append(f"    static constexpr {type_str} {constName} = {rhs};")
        out.append("};")
        out.append("")
    return("\n".join(out))


def _configSymSpelling(prj, memberNames):
    """Per-symbol speller for an eval-derived constant emitted inside a Config
    struct. A referent that is itself a struct member (a parameterizable sibling,
    declared earlier in dependency order) stays symbolic as its bare member name,
    so the variant's own value drives the computation; any other referent is a
    non-parameterizable constant spelled from its persisted value as a literal."""
    def symSpelling(symKey):
        if symKey in prj.data['constants']:
            row = prj.data['constants'][symKey]
            name = row['constant']
            if name in memberNames:
                return name
        return str(prj.getConst(symKey))
    return symSpelling


def _configMemberRhs(constData, resolved, symSpelling):
    """RHS for one Config struct member. An eval-derived parameterizable constant
    (non-empty evalCanonical) is emitted symbolically from its canonical
    expression so each variant recomputes it from that struct's own members; a
    backing block-param constant emits its per-variant resolved value."""
    if constData['evalCanonical']:
        return emitCStyleCanonical(constData['evalCanonical'], symSpelling)
    return resolved


def _config_type(value):
    valueType = value['valueType']
    if valueType == 'uint':
        maxValue = max(value['value'], value['maxValue'])
        return 'uint32_t' if maxValue <= 0xFFFFFFFF else 'uint64_t'
    if valueType == 'int':
        maxAbs = max(abs(value['value']), abs(value['maxValue']))
        return 'int32_t' if maxAbs <= 0x7FFFFFFF else 'int64_t'
    if valueType == 'real':
        return 'double'
    return valueType
