
import textwrap

from  pysrc.processYaml import camelCase

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
    instName=camelCase('u', blockName)
    s = t.render(blockname=blockName, dutinstname=instName)
    return s

def tb_sec_header(args, prj, data):
    t = Template(sec_tb_class_header_template)
    blockName=data['blockName']
    instName=camelCase('u', blockName)
    s = t.render(blockname=blockName, dutinstname=instName)
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

    return "\n".join(out)

def ext_sec_body(args, prj, data):

    out = []

    indent = ' '*4

    out.append('{')

    if data.get('cinst', None):
        for _,data_ in data['connections'].items():
            intfName = data_['interfaceName']
            instPortName = data_['interfaceName']
            if data['cinst'] not in [ data_['src'], data_['dst']]:
                continue
            elif data['cinst'] == data_['src']:
                instName = data_['dst']
                if data_['dstport']:
                    instPortName = data_['dstport']
            elif data['cinst'] == data_['dst'] :
                instName = data_['src']
                if data_['srcport']:
                    instPortName = data_['srcport']
            s = '{instName}->{instPortName}({intfName});'
            out.append(indent + s.format(instName=instName, instPortName=instPortName, intfName=intfName))

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

    t = Template(sec_tb_external_header_template)
    s = t.render(
        blockname=args.block, cinst=data.get('cinst', None),
        ext_fwd_decl='\n'.join(ext_fwd_decl_s),
        ext_inst_decl='\n'.join(ext_inst_decl_s)
    )
    return(s)

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
    {{blockname}}External uExternal;

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
        ,uExternal("uExternal")
{
    bind({{dutinstname}}.get(), &uExternal);
}
"""

sec_tb_external_header_template = """\

#include "{{blockname}}Base.h"

{%- if cinst %}

//contained instances forward class declaration
{{ext_fwd_decl}}
{%- endif %}

class {{blockname}}External: public sc_module, public {{blockname}}Inverted {

    logBlock log_;

public:

{%- if cinst %}

    {{ ext_inst_decl | indent(4) }}
{%- endif %}

    SC_HAS_PROCESS ({{blockname}}External);

    {{blockname}}External(sc_module_name modulename);

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