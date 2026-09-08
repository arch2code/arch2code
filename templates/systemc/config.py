import pysrc.emissionUtils as emissionUtils
from pysrc.intf_gen_utils import cpp_config_module_name, CONTAINER_CONFIG_PARAM

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # A registrar-domain Config module has --parent on its param line; the
    # context-mode header does not.
    if 'parent' in data:
        return(configModule(args, prj, data))
    return(includeConfig(args, prj, data))


def configModule(args, prj, data):
    view = prj.getConfigModuleData(data['qualBlock'], data['parent'])
    descriptors = view['descriptors']
    if not descriptors:
        return ""
    # All descriptors share one (project, block) identity, so any one names the module.
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
    for desc in descriptors:
        out.extend(_descriptorStructOpen(desc, desc['structName'], export=True))
        out.extend(_descriptorMemberLines(prj, desc))
        out.append("};")
        out.append("")
    return("\n".join(out))


def _descriptorStructOpen(desc, structName, export):
    """Opening line(s) of one per-variant Config struct.

    A variant every one of whose parameters is bound to a value emits a plain
    struct. A variant that sources any parameter from its container emits a
    class TEMPLATE over the container's Config, because the value is not known
    where the variant is declared: it is whatever the container it is
    instantiated in was configured at. One template is emitted per declared
    (block, variant) however many sites instantiate it."""
    prefix = 'export ' if export else ''
    if desc['containerSourced']:
        return [f'{prefix}template<typename {CONTAINER_CONFIG_PARAM}>',
                f'struct {structName} {{']
    return [f'{prefix}struct {structName} {{']


def _descriptorMemberLines(prj, desc):
    """Member lines of one Config struct. Backing constants are looked up by
    paramSourceKeys, so a same-spelled param in another block cannot supply the type."""
    out = []
    variantSpelling = _configSymSpelling(prj, set(desc['values'].keys()))
    for constName, resolved in desc['values'].items():
        containerParam = desc['containerSourced'].get(constName)
        constData = prj.data['constants'][desc['paramSourceKeys'][constName]]
        if containerParam:
            rhs = f'{CONTAINER_CONFIG_PARAM}::{containerParam}'
        else:
            rhs = _configMemberRhs(constData, resolved, variantSpelling)
        out.append(f"    static constexpr {_config_type(constData)} {constName} = {rhs};")
    return out


def emitCStyleCanonical(evalCanonical, symSpelling):
    """Translate a persisted canonical eval expression into a C/C++ expression
    string suitable for the RHS of a constexpr or firmware-header initializer
    (see emissionUtils.emitExpr)."""
    return emissionUtils.emitExpr(evalCanonical, symSpelling, emissionUtils.C)


def configStructLines(prj, data, structName, baseValues):
    """Emit lines for one Config struct given base-value overrides. Covers
    every parameterizable constant this context's structures need for
    round-trip testing (projectOpen._sampleConfigConstants), not the
    narrower per-block set the real build emits."""
    params = list(data['sampleConfigConstants'].values())
    spelling = _configSymSpelling(prj, {value['constant'] for value in params})
    out = [f"struct {structName} {{"]
    for value in params:
        type_str = _config_type(value)
        rhs = _configMemberRhs(value, baseValues.get(value['constant'], value['value']), spelling)
        out.append(f"    static constexpr {type_str} {value['constant']} = {rhs};")
    out.append("};")
    return out


def includeConfig(args, prj, data):
    # The context-mode Config header stays scaffolded but carries nothing;
    # Config structs live in the registrar-domain module (configModule).
    return ""


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
