import textwrap
import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import roundup_multiple

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
        case _ : return 'xx'

    return s

def get_include_deps(prj, data):
    include_deps = []
    include_deps.append(prj.getModuleFilename('blockBase', data["blockName"], 'hdr'))
    for context in data['includeContext']:
        if context in data['includeFiles']['include_hdr']:
            include_deps.append(data["includeFiles"]["include_hdr"][context]["baseName"])
    return include_deps

def get_reghandler_properties(prj, data):
    reghandler = dict()
    rhd = data['addressDecode']
    reghandler = {
        "port_name": rhd['registerBusInterface'],
        "addr_type" : rhd['registerBusStructs']['addr_t'],
        "data_type" : rhd['registerBusStructs']['data_t'],
        "addressmask" : f"(1<<({rhd['addressBits']}))-1"
    }
    return reghandler

def get_hwregs(prj, data):
    hwregs = []
    regs = dict()

    sorted_insts = sorted(list(data['memoryPorts'].values()) + list(data['registerPorts'].values()), key=lambda x: x['offset'])

    for inst in sorted_insts:
        if 'memory' in inst:
            hwregs.append({
                "is_memory": True,
                "name": inst['memory'] + '_adapter',
                "datatype": inst['structure'],
                "addresstype": inst['addressStruct'],
                "word_lines": inst['wordLines'],
                "offset": hex(inst['offset']),
                "port_name": inst['memory'],
                "descr": inst['desc']
            })
        elif inst.get('regType') == 'memory':
            hwregs.append({
                "is_memory": True,
                "name": inst['register'] + '_adapter',
                "datatype": inst['structure'],
                "addresstype": inst['addressStruct'],
                "word_lines": inst['wordLines'],
                "offset": hex(inst['offset']),
                "port_name": inst['register'],
                "descr": inst['desc']
            })
        else:
            port_type = intf_gen_utils.get_intf_type(inst['interfaceType'], data)
            direction = "_out" if inst['direction'] == 'src' else "_in"
            port_type = port_type + direction
            hwregs.append({
                "is_memory": False,
                "name": inst['register'] + '_reg',
                "datatype": inst['structure'],
                "size_rounded": roundup_multiple(inst['bytes'], 4),
                "size": inst['bytes'],
                "ro" : 'true' if inst['regType'] == 'ro' else 'false',
                "offset": hex(inst['offset']),
                "port_type": port_type,
                "port_name": inst['register'],
                "default": hex(prj.getConst(inst['defaultValue'])) if inst['regType'] == 'rw' else None,
                "descr": inst['desc']
            })
    return hwregs

def render_section_header(args, prj, data):
    t = Template(block_regs_header_template)
    blockName=data['blockName']
    s = t.render(blockname=blockName, include_deps=get_include_deps(prj, data), hwregs=get_hwregs(prj, data))
    return s

def render_section_init(args, prj, data):
    t = Template(block_regs_init_section_template)
    blockName=data['blockName']
    # render the template with the variables
    s = t.render(blockname=blockName, reghandler=get_reghandler_properties(prj, data), hwregs=get_hwregs(prj, data))
    return s.rstrip()

def render_section_body(args, prj, data):
    t = Template(block_regs_body_section_template)
    blockName=data['blockName']
    # render the template with the variables
    s = t.render(blockname=blockName, hwregs=get_hwregs(prj, data))
    return s.rstrip()

block_regs_header_template = '''\
#include "logging.h"
#include "instanceFactory.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
{% for entry in include_deps -%}
#include "{{entry}}"
{% endfor %}
SC_MODULE({{blockname}}), public blockBase, public {{blockname}}Base
{
private:
    void regHandler(void);
    addressMap regs;

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("{{blockname}}_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{{blockname}}>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

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
#include "{{blockname}}.h"

SC_HAS_PROCESS({{blockname}});

{{blockname}}::registerBlock {{blockname}}::registerBlock_; //register the block with the factory

void {{blockname}}::regHandler(void) { //handle register decode
    registerHandler< {{reghandler.addr_type}}, {{reghandler.data_type}} >(regs, {{reghandler.port_name}}, {{reghandler.addressmask}});
}

{{blockname}}::{{blockname}}(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("{{blockname}}", name(), bbMode)
        ,{{blockname}}Base(name(), variant)
        ,regs(log_)
        {% for entry in hwregs -%}
        {% if entry.is_memory -%}
        ,{{entry.name}}({{entry.port_name}})
        {% elif entry.default -%}
        ,{{entry.name}}(&{{entry.port_name}}, {{entry.datatype}}::_packedSt({{entry.default}}))
        {% else -%}
        ,{{entry.name}}(&{{entry.port_name}})
        {% endif -%}
        {% endfor -%}
'''

block_regs_body_section_template = '''\
{
    {% set memory_items = hwregs | selectattr('is_memory', 'equalto', true) | list -%}
    {% if memory_items -%}
    // register memories for FW access
    {% for entry in memory_items -%}
    regs.addMemory({{entry.offset}}, {{entry.datatype}}::_byteWidth, {{entry.word_lines}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor -%}
    {% endif -%}
    {% set register_items = hwregs | rejectattr('is_memory', 'equalto', true) | list -%}
    {% if register_items -%}
    // register registers for FW access
    {% for entry in register_items -%}
    regs.addRegister({{entry.offset}}, {{entry.size}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor -%}
    {% endif -%}
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
'''
