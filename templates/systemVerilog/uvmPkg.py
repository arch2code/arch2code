# The variant package of a hasUvm block. SV cannot parameterize a package, so
# the package binds the variant's parameter values as localparams and declares
# the block's parameterized types from them. The testbench interfaces and the
# agents must be typed by these package types: a struct declared locally in a
# module is a different type, and its virtual interface does not assign to one
# typed by the package.
import textwrap

from pysrc.systemVerilogGeneratorHelper import importPackages
from templates.systemVerilog.package import parameterizedDeclLines


def render(args, prj, data):
    # A block without params has one variantless top, which its scaffold
    # names with no --variant.
    variant = args.variant or ''
    top = data['uvm']['tops'][variant]
    match args.section:
        case 'header':
            out = render_header(args, prj, data, top)
        case 'items':
            out = render_items(prj, data, variant)
        case 'footer':
            out = f"\nendpackage : {top['pkgName']}\n"
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, items or footer")
    return textwrap.indent(out, ' '*args.sectionindent)


def render_header(args, prj, data, top):
    intfTypes = dict.fromkeys(port['interfaceType'] for port in data['uvm']['ports'])
    out = f"\npackage {top['pkgName']};\n"
    lines = ['import uvm_pkg::*;', '`include "uvm_macros.svh"']
    lines += [f'import {intfType}_uvm_pkg::*;' for intfType in intfTypes]
    lines.append(importPackages(args, prj, data['blockInfo']['_context'], data))
    out += textwrap.indent('\n'.join(lines), ' '*4) + '\n'
    return out


def param_args(port):
    # Unbound optional parameters keep the class and interface defaults.
    return ', '.join(f".{b['structureType']}({b['structure']})"
                     for b in port['paramBindings'] if not b['isNull'])


def render_items(prj, data, variant):
    lines = list()
    if data['blockInfo']['params']:
        values = data['standaloneVariants'][variant]
        lines += [f"localparam {p['param']} = {values[p['param']]};" for p in data['blockInfo']['params']]
        lines += [decl['line'] for decl in parameterizedDeclLines(
            data['parameterizedDecls'], prj, data['blockInfo']['params'])]
        lines.append('')
    for port in data['uvm']['ports']:
        name = port['name']
        intfType = port['interfaceType']
        params = param_args(port)
        lines.append(f"typedef {intfType}_agent #({params}) {name}_agent_t;")
        lines.append(f"typedef {name}_agent_t::item_t {name}_item_t;")
        lines.append(f"typedef {name}_agent_t::config_t {name}_config_t;")
        lines.append(f"typedef virtual {intfType}_if #({params}) {name}_vif_t;")
    return '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'
