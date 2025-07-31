import textwrap

from jinja2 import Template

# args from generator line
# prj object
# data set dict

def render(args, prj, data):

    return textwrap.indent(render_sc(args, prj, data), ' '*args.sectionindent)

def render_sc(args, prj, data):

    # FIXME force blockName to debayer_regs
    data['blockName'] = "debayer_regs"

    match args.section:
        case 'header': return render_section_header(args, prj, data)
        case 'init' : return render_section_init(args, prj, data)
        case 'body': return render_section_body(args, prj, data)
        case _ : return 'xx'

    return s

def get_include_deps(prj, data):
    # FIXME force include_deps of debayer_regs
    include_deps = [ "debayer_regsBase.h", "debayerIncludes.h", "shared_typesIncludes.h" ]
    return include_deps

def get_reghandler_properties(prj, data):
    # FIXME force reg_handler of debayer_regs
    reghandler = { "port_name": "cpu_apb_reg", "addr_type" : "apb_addr_t", "data_type" : "apb_data_t", "addressmask" : "(1<<(25-1))-1" }
    return reghandler

def get_hwregs(prj, data):
    hwregs = [ # FIXME force hwregs of debayer_regs
        { "name" : "bayer_pattern_reg", "datatype": "bayer_pattern_reg_t", "size": 4, "address" : "0x0", "port_type" : "status_out", "port_name" : "bayer_pattern", "descr" : "Bayer Pattern" },
        { "name" : "debayer_enable_reg", "datatype": "debayer_enable_reg_t", "size": 4, "address" : "0x8", "port_type" : "status_out", "port_name" : "debayer_enable", "descr" : "Debayer Enable" }
    ]
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
        hwRegisterIf< {{entry.datatype}}, {{entry.port_type}}<{{entry.datatype}}>, {{entry.size}}> {{entry.name}}; // {{entry.descr}}
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
        regs.addRegister({{entry.address}}, {{entry.size//4}}, "{{entry.port_name}}", &{{entry.name}} );
    {% endfor %}
    SC_THREAD(regHandler);
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
'''
