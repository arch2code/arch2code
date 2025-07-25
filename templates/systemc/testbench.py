
import textwrap

from  pysrc.processYaml import camelCase
from pysrc.intf_gen_utils import sc_gen_block_channels

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

    if data.get('cinst', None):
        external_blocks = set([v['instanceType'] for v in data['subBlockInstances'].values() if v['instance'] != data['cinst']])
        for blockName in sorted(external_blocks):
            s = '#include "{blockName}Base.h"'
            out.append(s.format(blockName=blockName))

    s = """
{blockName}External::{blockName}External(sc_module_name modulename) :
    {blockName}Inverted("Chnl"),
    log_(name())"""
    out.append(s.format(blockName=args.block))

    if data.get('cinst', None):
        for data_ in [v for v in data['subBlockInstances'].values() if v['instance'] != data['cinst']]:
            s = '   ,{instName}(std::dynamic_pointer_cast<{blockName}Base>( instanceFactory::createInstance(name(), "{instName}", "{blockName}", "")))'
            out.append(s.format(blockName=data_['instanceType'], instName=data_['instance']))

    if data.get('cinst', None):
        for _,data_ in data['connections'].items():
            if data['cinst'] in [ data_['src'], data_['dst'] ]:
                continue
            srcInst = data_['src']
            chnlData = sc_gen_block_channels(data_, prj)
            s = '   ,{chnlName}("{chnlName}", "{instName}")'
            out.append(s.format(chnlName=chnlData['chnl_name'], instName=srcInst))

    return "\n".join(out)

def ext_sec_body(args, prj, data):

    out = []

    indent = ' '*4

    out.append('{')

    if data.get('cinst', None):
        for _,data_ in data['connections'].items():
            chnlName = data_['channelName']
            instPortName = data_['interfaceName']
            if data['cinst'] == data_['src']:
                instName = data_['dst']
                if data_['dstport']:
                    instPortName = data_['dstport']
            elif data['cinst'] == data_['dst'] :
                instName = data_['src']
                if data_['srcport']:
                    instPortName = data_['srcport']
            else:
                continue
            s = '{instName}->{instPortName}({chnlName});'
            out.append(indent + s.format(instName=instName, instPortName=instPortName, chnlName=chnlName))

        for _,data_ in data['connections'].items():
            if data['cinst'] in [ data_['src'], data_['dst'] ]:
                continue
            chnlName = data_['channelName']
            for _,ends_ in data_['ends'].items():
                instName = ends_['instance']
                instPortName = ends_['portName']
                s = '{instName}->{instPortName}({chnlName});'
                out.append(indent + s.format(instName=instName, instPortName=instPortName, chnlName=chnlName))

    return "\n".join(out)

def ext_sec_header(args, prj, data):

    ext_fwd_decl_s = []
    if data.get('cinst', None):
        external_blocks = set([v['instanceType'] for v in data['subBlockInstances'].values() if v['instance'] != data['cinst']])
        for blockName in sorted(external_blocks):
            ext_fwd_decl_s.append(f'class {blockName}Base;')

    ext_inst_decl_s = []
    if data.get('cinst', None):
        external_insts = [v for v in data['subBlockInstances'].values() if v['instance'] != data['cinst']]
        for data_ in external_insts:
            s = 'std::shared_ptr<{blockName}Base> {instName};'
            ext_inst_decl_s.append(s.format(blockName=data_['instanceType'], instName=data_['instance']))

    ext_chnl_decl_s = []
    if data.get('cinst', None):
        for _,data_ in data['connections'].items():
            if data['cinst'] in [ data_['src'], data_['dst'] ]:
                continue
            chnlData = sc_gen_block_channels(data_, prj)
            ext_chnl_decl_s.append(chnlData['channel_decl'])

    t = Template(sec_tb_external_header_template)
    s = t.render(
        blockname=args.block, cinst=data.get('cinst', None),
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
    if data.get('cinst', None):
        # Rename interface if necessary
        # Gather all port names for cinst
        cinst_ports = set()
        for _,data_ in data['connections'].items():
            for _,ends_ in data_['ends'].items():
                if data['cinst'] in ends_['instance']:
                    cinst_ports.add(ends_['portName'])
                    data_['channelName'] = ends_['portName']

        # Now rename the interface names if duplicated
        for _,data_ in data['connections'].items():
            if data_['channelName'] in cinst_ports:
                f = list(filter(lambda x: x['instance'] == data['cinst'], data_['ends'].values()))
                if len(f) == 0:
                    # Alter the duplicated channel to avoid clash
                    data_['channelName'] = data_['channelName'] + '_'

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

    {{ ext_chnl_decl | indent(4) }}
{%- endif %}

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