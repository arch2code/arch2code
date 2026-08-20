from pysrc.systemVerilogGeneratorHelper import importPackages
import pysrc.emissionUtils as emissionUtils

# args from generator line
# prj object
# data set dict
def typeWidthExpression_sv(value, prj_data):
    """Build a SystemVerilog bit-range width expression for a type (goes in
    [expr-1:0]). Delegates the language-neutral width decision tree to
    emissionUtils.typeWidthExpr, binding SV constant spelling (the raw
    parameter/localparam name) and the SV literal-width fallback
    (value['realwidth']). Accepts either a raw constants dict or a prj."""
    constants = prj_data if isinstance(prj_data, dict) else prj_data.data['constants']
    return emissionUtils.typeWidthExpr(
        value, emissionUtils.SV,
        constSpelling=lambda key: constants[key]['constant'],
        literalWidth=lambda v: str(v['realwidth']))


def emitSvCanonical(evalCanonical, symSpelling):
    """Translate a persisted canonical eval expression into the SystemVerilog
    RHS of a module-local localparam (see emissionUtils.emitExpr)."""
    return emissionUtils.emitExpr(evalCanonical, symSpelling, emissionUtils.SV)


def parameterizedDeclLines(parameterizedDecls, prj, blockParams):
    """Module-local SV declaration lines for a block's parameterized
    declaration set (deriveParameterizedDeclSets), ordered by orderIndex
    (eval-derived localparams first, then types/sub-structures before the
    structures that use them, so a localparam referenced by a type width or
    struct array size is declared ahead of it). SV cannot parameterize a package, so a parameterized
    block declares these inside the owning module from its module parameters;
    they are the same declarations the package omits.

    Returns one entry per physical line, each a dict with 'declKind' and 'line'
    (the module-body declaration text, no leading indent). Constant entries also
    carry 'name' and 'rhs' (the localparam name and its expression) so a caller
    can re-emit them as a comma-separated parameter-port-list localparam when a
    port width must resolve them ahead of the port list.

    `blockParams` is the owning block's param rows. Each is keyed by its
    paramSource link - the backing constant's own key - because the symbols being
    spelled are constant keys; paramKey qualifies the param name with the file
    declaring the block and matches only when the two coincide.
    A symbol that is one of the block's params stays symbolic (its SV parameter
    name). A symbol already selected as an earlier localparam in this declaration
    set is spelled by that localparam name. Any other symbol is spelled from its
    persisted constant value as an SV literal."""
    paramNameByKey = {p['paramSourceKey']: p['param'] for p in blockParams}
    localConstNameByKey = {
        decl['declKey']: decl['body']['constant']
        for decl in parameterizedDecls
        if decl['declKind'] == 'constant'
    }

    def symSpelling(symKey):
        if symKey in paramNameByKey:
            return paramNameByKey[symKey]
        if symKey in localConstNameByKey:
            return localConstNameByKey[symKey]
        return str(prj.getConst(symKey))

    def arraySizeExpression(varData):
        if varData['arraySize'] in (0, '0'):
            return ''
        if varData['arraySizeKey']:
            return symSpelling(varData['arraySizeKey'])
        return varData['arraySize']

    out = []
    for decl in parameterizedDecls:
        body = decl['body']
        if decl['declKind'] == 'type':
            widthExpr = typeWidthExpression_sv(body, prj)
            signedStr = " signed" if body['isSigned'] else ""
            out.append({'declKind': 'type',
                        'line': f"typedef logic{signedStr}[{widthExpr}-1:0] {body['type']}; //{body['desc']}"})
        elif decl['declKind'] == 'structure':
            out.append({'declKind': 'structure', 'line': "typedef struct packed {"})
            for var, varData in body['vars'].items():
                arrayExpr = arraySizeExpression(varData)
                arraySize = '' if arrayExpr == '' else f"[{arrayExpr}-1:0] "
                typeName = varData['subStruct'] if varData['entryType'] == 'NamedStruct' else varData['varType']
                out.append({'declKind': 'structure',
                            'line': f"    {typeName} {arraySize}{varData['variable']}; //{varData['desc']}"})
            out.append({'declKind': 'structure', 'line': f"}} {body['structure']};"})
        else:  # constant: eval-derived parameterizable constant -> localparam
            rhs = emitSvCanonical(body['evalCanonical'], symSpelling)
            out.append({'declKind': 'constant', 'name': body['constant'], 'rhs': rhs,
                        'line': f"localparam {body['constant']} = {rhs}; //{body['desc']}"})
    return out


def render(args, prj, data):
    out     = ''
    indent  = ' ' *4
    if data['context'] is None:
        return out
    packageName = prj.contextModuleIdentity[data['context'][0]] + '_package'

    out += f"package {packageName};\n"
    pkg_str = importPackages(args, prj, data['context'][0], data, excludeSelf=True) 
    if pkg_str:
        out += pkg_str + '\n'

    # Parameterizable declarations are emitted in module scope, not the
    # package (SV cannot parameterize packages), so they are skipped here.
    # Now put in everything at this context level
    # Generate constants as localparam[s]
    for unusedKey, value in data['constants'].items():
        if value['isParameterizable']:
            continue
        match value['valueType']:
            case 'uint':
                if value['value'] <= 0xFFFFFFFF:
                    type_str = 'int unsigned'
                    value_str = f"32'h{value['value']:09_X}"
                else:
                    type_str = 'longint unsigned'
                    value_str = f"64'h{value['value']:019_X}"
            case 'int':
                if abs(value['value']) <= 0x7FFFFFFF:
                    type_str = 'int'
                    if value['value'] < 0:
                        value_str = f"-32'sh{abs(value['value']):09_X}"
                    else:
                        value_str = f"32'sh{value['value']:09_X}"
                else:
                    type_str = 'longint'
                    if value['value'] < 0:
                        value_str = f"-64'sh{abs(value['value']):019_X}"
                    else:
                        value_str = f"64'sh{value['value']:019_X}"
            case 'real':
                type_str = 'real'
                value_str = f"{value['value']}"
            case _:
                type_str = value['valueType']
                value_str = f"{value['value']}"
        out += f"localparam {type_str} {value['constant']} = {value_str};  // {value['desc']}\n"
    # Generate types
    out += f"\n// types\n"
    for unusedKey, value in data['types'].items():
        if value['isParameterizable']:
            continue
        widthExpr = typeWidthExpression_sv(value, prj.data['constants'])
        desc = value['desc']
        # Check if type is signed
        isSigned = value['isSigned']
        signedStr = " signed" if isSigned else ""
        out += f"typedef logic{signedStr}[{widthExpr}-1:0] {value['type']}; //{desc}\n"

    # Generate enums
    out += f"\n// enums\n"
    for unusedKey, value in data['enums'].items():
        if value['isParameterizable']:
            continue
        try:
            width = max(int(value['width']), 1)
        except (ValueError, TypeError):
            width = value['width']
            if value['width'] in prj.data['constants']:
                width = prj.data['constants'][value['width']]['constant']
        out += f"typedef enum logic[{width}-1:0] {{ {' '*value['descSpaces']}//{value['desc']}\n"
        # below loop processes enums and puts a comma after them for all in the list but the last one
        for enumData in value['enum'][:-1]:
            out += f"{indent}{enumData['enumName']} = {enumData['value']}, {' '*enumData['descSpaces']}// {enumData['desc']}\n"
        # this statement is similar to the loop but we are printing the last element in the list without a comma
        #   this style is pythonic and may look a little messy at first
        out += f"{indent}{value['enum'][-1]['enumName']} = {value['enum'][-1]['value']} {' '*value['enum'][-1]['descSpaces']}// {value['enum'][-1]['desc']}\n"
        # finally delcare the enum type and move on to any more enums or finish
        out += f"}} {value['type']};\n"

    # Generate structures
    out += f"\n// structures\n"
    for struct, value in data['structures'].items():
        if value['isParameterizable']:
            continue
        out += f"typedef struct packed {{\n"
        for var, varData in value['vars'].items():
            if varData['arraySize'] == 0 or varData['arraySize'] == '0':
                arraySize = ''
            else:
                arraySize = f"[{varData['arraySize']}-1:0] "
            if varData['entryType'] == 'NamedVar' or varData['entryType'] == 'NamedType':
                out += f"{indent}{varData['varType']} {arraySize}{varData['variable']}; //{varData['desc']}\n"
            else: # varData['entryType'] == 'NamedStruct'
                out += f"{indent}{varData['subStruct']} {arraySize}{varData['variable']}; //{varData['desc']}\n"
        out += f"}} {value['structure']};\n\n"

    out += f"endpackage : {packageName}"

    return (out)
