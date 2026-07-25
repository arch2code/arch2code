import textwrap
import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import roundup_multiple
from templates.systemc.constructor import blockRegistrarInitLines

from jinja2 import Template

# args from generator line
# prj object
# data set dict

def render(args, prj, data):

    return textwrap.indent(render_sc(args, prj, data), ' '*args.sectionindent)

def render_sc(args, prj, data):


    match args.section:
        case 'header': return render_section_header(args, prj, data)
        case 'init' : return render_section_init(args, prj, data)
        case 'body': return render_section_body(args, prj, data)
        case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, init, body")

    return s

def get_include_deps(args, prj, data):
    # Classic-mode header include set for the reg-handler. Reuse the shared
    # class-dependency computation so the reg-handler header inherits exactly the
    # same channel headers, framework headers (addressMap/hwRegister/hwMemory),
    # config-policy includes, and context imports as a normal block class
    # (classDecl), preventing include-set drift. Rendered as the flat `line` of
    # each (kind, line) pair. In module mode the block-module global module
    # fragment (moduleScaffold.blockModuleHeader) owns these instead, so
    # render_section_header suppresses this set entirely.
    return [line for (kind, line) in intf_gen_utils.sc_class_dependency_includes(args, prj, data)]

def get_reghandler_properties(prj, data):
    reghandler = dict()
    rhd = data['addressDecode']
    reghandler = {
        "port_name": rhd['registerBusPort'],
        "addr_type" : rhd['registerBusStructs']['addr_t'],
        "data_type" : rhd['registerBusStructs']['data_t'],
        "addressmask" : f"(1<<({rhd['addressBits']}))-1"
    }
    return reghandler

def address_const_name(data, inst, name_field):
    block_name = inst.get('block', data['blockName'])
    return f"REG_ADDR_{block_name.upper()}_{inst[name_field].upper()}"

def get_hwregs(prj, data):
    hwregs = []
    regs = dict()

    sorted_insts = sorted(list(data['memoryPorts'].values()) + list(data['registerPorts'].values()), key=lambda x: x['offset'])

    for inst in sorted_insts:
        if 'memory' in inst:
            const_name = address_const_name(data, inst, 'memory')
            hwregs.append({
                "is_memory": True,
                "name": inst['memory'] + '_adapter',
                "datatype": inst['structure'],
                "addresstype": inst['addressStruct'],
                "word_lines": inst['wordLines'],
                "offset": const_name,
                "offset_value": hex(inst['offset']),
                "const_name": const_name,
                "port_name": inst['memory'],
                "descr": inst['desc']
            })
        elif inst.get('regType') == 'memory':
            const_name = address_const_name(data, inst, 'register')
            hwregs.append({
                "is_memory": True,
                "name": inst['register'] + '_adapter',
                "datatype": inst['structure'],
                "addresstype": inst['addressStruct'],
                "word_lines": inst['wordLines'],
                "offset": const_name,
                "offset_value": hex(inst['offset']),
                "const_name": const_name,
                "port_name": inst['register'],
                "descr": inst['desc']
            })
        else:
            const_name = address_const_name(data, inst, 'register')
            effective_bytes = inst.get('maxBytes', inst['bytes'])
            port_type = intf_gen_utils.get_intf_type(inst['interfaceType'], data)
            direction = "_out" if inst['direction'] == 'src' else "_in"
            port_type = port_type + direction
            hwregs.append({
                "is_memory": False,
                "name": inst['register'] + '_reg',
                "datatype": inst['structure'],
                "size_rounded": roundup_multiple(effective_bytes, 4),
                "size": inst['bytes'],
                "ro" : 'true' if inst['regType'] == 'ro' else 'false',
                "offset": const_name,
                "offset_value": hex(inst['offset']),
                "const_name": const_name,
                "port_type": port_type,
                "port_name": inst['register'],
                "default": hex(prj.getConst(inst['defaultValue'])) if inst['regType'] == 'rw' else None,
                "descr": inst['desc']
            })
    return hwregs

def render_section_header(args, prj, data):
    t = Template(block_regs_header_template)
    blockName=data['blockName']
    # Only leaf parameterizable reg-handlers (those that inherit the parent's
    # own `params:`) are class templates; mirror classDecl/constructor's
    # hasOwnParams gate so non-parameterizable reg-handlers stay non-templated.
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    templatePrefix = intf_gen_utils.block_config_decl(hasOwnParams)
    if templatePrefix:
        templatePrefix += '\n'
    # In module mode the block-module global module fragment
    # (moduleScaffold.blockModuleHeader) owns the framework/context includes and
    # the class is exported from the module; classic mode emits the includes
    # inline ahead of the (non-exported) class.
    moduleMode = (args.mode == 'module')
    exportKw = 'export ' if moduleMode else ''
    include_deps = [] if moduleMode else get_include_deps(args, prj, data)
    s = t.render(blockname=blockName, cfg=cfg, templatePrefix=templatePrefix,
                 hasOwnParams=hasOwnParams, moduleMode=moduleMode, exportKw=exportKw,
                 include_deps=include_deps, hwregs=get_hwregs(prj, data))
    return s

def render_section_init(args, prj, data):
    t = Template(block_regs_init_section_template)
    blockName=data['blockName']
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    templatePrefix = intf_gen_utils.block_config_decl(hasOwnParams)
    if templatePrefix:
        templatePrefix += '\n'
    # In module mode the constructor bodies live in the same TU as the class
    # (the block-module `.cppm`), whose global module fragment owns the class
    # header self-include; a module interface forbids #include after
    # `export module`. Classic mode keeps emitting the self-include here.
    moduleMode = (args.mode == 'module')
    # Reuse the shared registration emission so parameterizable reg-handlers
    # defer factory registration to the per-block trampoline (Registrar TU) and
    # only emit instantiation anchors here, exactly as constructor.py does for
    # leaf parameterizable blocks.
    registration = '\n'.join(blockRegistrarInitLines(
        args, prj, data, blockName, hasOwnParams))
    reghandler = get_reghandler_properties(prj, data)
    # Inherited base ports are dependent names inside a class template, so they
    # must be reached through `this->`; non-templated reg-handlers use the bare
    # name unchanged.
    thisq = 'this->' if hasOwnParams else ''
    # render the template with the variables
    s = t.render(blockname=blockName, cfg=cfg, templatePrefix=templatePrefix,
                 hasOwnParams=hasOwnParams, moduleMode=moduleMode,
                 registration=registration, thisq=thisq,
                 reghandler=reghandler, hwregs=get_hwregs(prj, data))
    return s.rstrip()

def render_section_body(args, prj, data):
    t = Template(block_regs_body_section_template)
    blockName=data['blockName']
    # render the template with the variables
    s = t.render(blockname=blockName, hwregs=get_hwregs(prj, data))
    return s.rstrip()

block_regs_header_template = '''\
{% if not moduleMode -%}
{% for entry in include_deps -%}
{{entry}}
{% endfor %}
{% endif -%}
{{exportKw}}{{templatePrefix}}SC_MODULE({{blockname}}), public blockBase, public {{blockname}}Base{{cfg}}
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:
{% if hasOwnParams %}
    SC_HAS_PROCESS({{blockname}});
{% endif %}
    {{blockname}}(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~{{blockname}}() override = default;

    //registers
    {% for entry in hwregs -%}
    {% if entry.is_memory -%}
    hwMemoryPort< {{entry.addresstype}}, {{entry.datatype}} > {{entry.name}}; // {{entry.descr}}
    {% else -%}
    hwRegisterIf< {{entry.datatype}}, {{entry.port_type}}<{{entry.datatype}}>, {{entry.size_rounded}}, {{entry.ro}}> {{entry.name}}; // {{entry.descr}}
    {% endif -%}
    {% endfor %}
'''

block_regs_init_section_template = '''\
{% if not moduleMode -%}
#include "{{blockname}}.h"
{% endif -%}
{% if not hasOwnParams %}
SC_HAS_PROCESS({{blockname}});
{% endif %}
{{registration}}

{{templatePrefix}}void {{blockname}}{{cfg}}::regHandler(void) { //handle register decode
    registerHandler< {{reghandler.addr_type}}, {{reghandler.data_type}} >(_a2cRegs, {{thisq}}{{reghandler.port_name}}, {{reghandler.addressmask}});
}

{{templatePrefix}}{{blockname}}{{cfg}}::{{blockname}}(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("{{blockname}}", name(), bbMode)
        ,{{blockname}}Base{{cfg}}(name(), variant)
        ,_a2cRegs(log_)
        {% for entry in hwregs -%}
        {% if entry.is_memory -%}
        ,{{entry.name}}({{thisq}}{{entry.port_name}})
        {% elif entry.default -%}
        ,{{entry.name}}(&{{thisq}}{{entry.port_name}}, {{entry.datatype}}::_packedSt({{entry.default}}))
        {% else -%}
        ,{{entry.name}}(&{{thisq}}{{entry.port_name}})
        {% endif -%}
        {% endfor -%}
'''

block_regs_body_section_template = '''\
{
    {% if hwregs -%}
    // Generated register/memory address offsets
    {% for entry in hwregs -%}
    constexpr uint64_t {{entry.const_name}} = {{entry.offset_value}};
    {% endfor %}
    {% endif -%}
    {% set memory_items = hwregs | selectattr('is_memory', 'equalto', true) | list -%}
    {% if memory_items -%}
    // register memories for FW access
    {% for entry in memory_items -%}
    _a2cRegs.addMemory({{entry.offset}}, {{entry.datatype}}::_byteWidth, {{entry.word_lines}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor -%}
    {% endif -%}
    {% set register_items = hwregs | rejectattr('is_memory', 'equalto', true) | list -%}
    {% if register_items -%}
    // register registers for FW access
    {% for entry in register_items -%}
    _a2cRegs.addRegister({{entry.offset}}, {{entry.size}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor -%}
    {% endif -%}
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
'''
