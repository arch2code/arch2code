import pysrc.emissionUtils as emissionUtils
from pysrc.intf_gen_utils import CONTAINER_CONFIG_PARAM, configType

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    return(configModule(args, prj, data))


def configModule(args, prj, data):
    view = prj.getConfigModuleData(data['qualBlock'], data['parent'])
    descriptors = view['descriptors']
    if not descriptors:
        return ""
    # All descriptors share one (project, block) identity, so any one names the module.
    moduleName = descriptors[0]['configModule']
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
    for constName, resolved in desc['values'].items():
        containerParam = desc['containerSourced'].get(constName)
        constData = prj.data['constants'][desc['paramSourceKeys'][constName]]
        rhs = f'{CONTAINER_CONFIG_PARAM}::{containerParam}' if containerParam else resolved
        out.append(f"    static constexpr {configType(constData)} {constName} = {rhs};")
    return out


def emitCStyleCanonical(evalCanonical, symSpelling):
    """Translate a persisted canonical eval expression into a C/C++ expression
    string suitable for the RHS of a constexpr or firmware-header initializer
    (see emissionUtils.emitExpr)."""
    return emissionUtils.emitExpr(evalCanonical, symSpelling, emissionUtils.C)


def configStructLines(data, structName, baseValues):
    """Lines for one sample Config struct, one literal member per root
    parameter the context's structures need (projectOpen._sampleConfigConstants)
    at this sample point's values."""
    out = [f"struct {structName} {{"]
    for value in data['sampleConfigConstants'].values():
        out.append(f"    static constexpr {configType(value)} {value['constant']} = {baseValues[value['constant']]};")
    out.append("};")
    return out
