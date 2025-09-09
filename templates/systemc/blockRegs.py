import textwrap

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
        "addressmask" : f"(1<<({rhd['addressBits']}-1))-1"
    }
    return reghandler

def get_hwregs(prj, data):
    hwregs = []
    for reg in data['registers'].values():
        hwregs.append({
            "name": reg['register'] + '_reg',
            "datatype": reg['structure'],
            "size": reg['bytes']*4,
            "ro" : 'true' if reg['regType'] == 'ro' else 'false',
            "offset": hex(reg['offset']),
            "port_type": reg['interfaceType'] + ('_in' if reg['regType'] == 'ro' else '_out'),
            "port_name": reg['register'],
            "descr": reg['desc']
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
        hwRegisterIf< {{entry.datatype}}, {{entry.port_type}}<{{entry.datatype}}>, {{entry.size}}, {{entry.ro}}> {{entry.name}}; // {{entry.descr}}
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
        ,{{entry.name}}(&{{entry.port_name}})
        {% endfor -%}
'''

block_regs_body_section_template = '''\
{
    // register registers for FW access
    {% for entry in hwregs -%}
        regs.addRegister({{entry.offset}}, {{entry.size//4}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor %}
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
'''
