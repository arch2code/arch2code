
import textwrap

from pysrc.processYaml import getPortChannelName
from pysrc.arch2codeHelper import printError
from pysrc.intf_gen_utils import sc_gen_block_channels, sc_connect_channels, sc_connect_channel_type, sc_instance_includes, sc_declare_channels, get_intf_type, get_intf_defs, inverse_portdir

from jinja2 import Template

# args from generator line
# prj object
# data set dict

def render(args, prj, data):

    return textwrap.indent(render_sc(args, prj, data), ' '*args.sectionindent)

def render_sc(args, prj, data):

    if (args.template == "testbench"):
        match args.section:
            case 'init' : return tb_sec_init(args, prj, data)
            case 'header': return tb_sec_header(args, prj, data)
            case _ : return 'xx'
    elif(args.template == "tbExternal"):
        refactor_tbExternal(args, prj, data)
        match args.section:
            case 'init' : return ext_sec_init(args, prj, data)
            case 'body': return ext_sec_body(args, prj, data)
            case 'header': return ext_sec_header(args, prj, data)
            case _ : return 'xx'
    elif(args.template == "tbConfig"):
        return tb_config_class(args, prj, data)
    else:
        return ' yy'

def tb_config_class(args, prj, data):
    t = Template(sec_tb_config_class_template)
    blockName=data['blockName']
    s = t.render(blockname=blockName)
    return s

def tb_sec_init(args, prj, data):
    t = Template(sec_tb_class_init_template)
    blockName=data['blockName']
    instName=blockName
    s = t.render(blockname=blockName, dutinstname=instName, extinstname="external")
    return s

def tb_sec_header(args, prj, data):
    t = Template(sec_tb_class_header_template)
    blockName=data['blockName']
    instName=blockName
    s = t.render(blockname=blockName, dutinstname=instName, extinstname="external")
    return s

def ext_sec_init(args, prj, data):

    out = []
    out += sc_instance_includes(data, prj)

    s = """
{blockName}External::{blockName}External(sc_module_name modulename) :
    {blockName}Inverted("Chnl"),
    log_(name())\n"""
    out.append(s.format(blockName=data['blockName']))

    for data_ in data['subBlockInstances'].values():
        s = '   ,{instName}(std::dynamic_pointer_cast<{blockName}Base>( instanceFactory::createInstance(name(), "{instName}", "{blockName}", "")))'
        out.append(s.format(blockName=data_['instanceType'], instName=data_['instance']))

    for channelType in data['connectDouble']:
        for _,data_ in data['connectDouble'][channelType].items():
            srcInst = data_['src']
            chnlData = sc_gen_block_channels(data_, prj)
            s = '   ,{chnlName}("{chnlName}", "{instName}")'
            out.append(s.format(chnlName=chnlData['chnl_name'], instName=srcInst))

    return "\n".join(out)

def ext_sec_body(args, prj, data):

    out = []

    indent = ' '*4

    out.append('{')
    prunedConnections = []
    port_names = set()
    # connect hierarchical ports that connect the excluded instances to the external blocks
    for key, value in data.get('prunedConnections', dict()).items():
        if (len(value['ends']) > 2):
            multiDst = get_intf_defs(get_intf_type(value['interfaceType'])).get('multiDst', False)
            if not multiDst:
                printError(f"connection {key} has more than 2 ends. Only status interfaces (including ro registers) can have multiple dst connections")
        for end, endvalue in value["ends"].items():
            port_name = getPortChannelName(value, inverse_portdir(endvalue['direction']) + 'port')
            port_names.add(port_name)
            prunedConnections.append(f'{indent}{ endvalue["instance"] }->{ endvalue["portName"]}({ port_name });')

    # resolve any port-channel name clashes
    for conn, conn_data in data.get('connections', dict()).items():
        if conn_data['interfaceName'] in port_names:
            conn_data['interfaceName'] = conn_data['interfaceName'] + '_'

    # channels outside of any that include the excluded instances
    connections = sc_connect_channels(data, indent)

    if connections or prunedConnections:
        out.append(indent +'// instance to instance connections via channel')
        out += connections
        out += prunedConnections

    out.append('\n' + indent +'SC_THREAD(eotThread);')

    return "\n".join(out)

def ext_sec_header(args, prj, data):

    ext_fwd_decl_s = []
    external_blocks = sorted(data['subBlocks'].values())
    for blockName in external_blocks:
        ext_fwd_decl_s.append(f'class {blockName}Base;')

    ext_inst_decl_s = []
    external_insts = [v for v in data['subBlockInstances'].values() ]
    for data_ in external_insts:
        ext_inst_decl_s.append(f'std::shared_ptr<{data_["instanceType"]}Base> {data_["instance"]};')

    ext_chnl_decl_s = sc_declare_channels(data, prj, ' '*4)

    t = Template(sec_tb_external_header_template)
    s = t.render(
        blockname=data['blockName'],
        ext_fwd_decl='\n'.join(ext_fwd_decl_s),
        ext_inst_decl='\n'.join(ext_inst_decl_s),
        ext_chnl_decl='\n'.join(ext_chnl_decl_s)
    )
    return(s)

"""
Refactor the external block connectivity to be used in the testbench
and avoid channel name clashes
"""
def refactor_tbExternal(args, prj, data):
    if len(data['excludedInstances']) > 0:
        blockname = data['excludedInstances'][next(iter(data['excludedInstances']))]['instanceType']
    else:
        blockname = data['blockName']
    data['blockName'] = blockname

sec_tb_class_header_template = """\
#include "systemc.h"
#include "instanceFactory.h"

#include "{{blockname}}Base.h"
#include "{{blockname}}External.h"

class {{blockname}}Testbench: public sc_module, public blockBase, public {{blockname}}Channels {

    private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("{{blockname}}Testbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{{blockname}}Testbench>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;

public:

    std::shared_ptr<{{blockname}}Base> {{dutinstname}};
    {{blockname}}External {{extinstname}};

    {{blockname}}Testbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~{{blockname}}Testbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
"""

sec_tb_class_init_template = """\
#include "{{blockname}}Testbench.h"

{{blockname}}Testbench::registerBlock {{blockname}}Testbench::registerBlock_; //register the block with the factory

{{blockname}}Testbench::{{blockname}}Testbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("{{blockname}}Testbench", name(), bbMode)
        ,{{blockname}}Channels("Chnl", "tb")
        ,{{dutinstname}}(std::dynamic_pointer_cast<{{blockname}}Base>( instanceFactory::createInstance(name(), "{{dutinstname}}", "{{blockname}}", "")))
        ,{{extinstname}}("{{extinstname}}")
{
    bind({{dutinstname}}.get(), &{{extinstname}});
}
"""

sec_tb_external_header_template = """\

#include "{{blockname}}Base.h"
#include "endOfTest.h"

{%- if ext_fwd_decl %}

//contained instances forward class declaration
{{ext_fwd_decl}}
{%- endif %}

class {{blockname}}External: public sc_module, public {{blockname}}Inverted {

    logBlock log_;

public:

{%- if ext_inst_decl %}

    {{ ext_inst_decl | indent(4) }}
{%- endif %}

    SC_HAS_PROCESS ({{blockname}}External);

    {{blockname}}External(sc_module_name modulename);

{%- if ext_chnl_decl %}

{{ ext_chnl_decl }}
{%- endif %}

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

"""

sec_tb_config_class_template = """\

class {{blockname}}Config : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("{{blockname}}", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<{{blockname}}Config>());}, is_default_testbench_v<{{blockname}}Config>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~{{blockname}}Config() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
"""