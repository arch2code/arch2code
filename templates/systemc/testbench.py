
import textwrap

from pysrc.processYaml import getPortChannelName
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.intf_gen_utils import sc_gen_block_channels, sc_connect_channels, sc_instance_includes, sc_declare_channels, get_intf_type, get_intf_defs, inverse_portdir, resolve_dut_variant_selection, sc_declare_thunkers, sc_thunker_protocols, _resolve_cross_interface_ends, _thunker_member_name, cpp_base_module_name, cpp_context_include_lines, cpp_config_arg, sc_channel_header_includes


def _tb_context_import_lines(prj, data):
    # A module import does not propagate the base module's own context imports /
    # using-directives the way the old textual `<block>Base.h` did. The testbench
    # and its External pseudo-block spell the DUT's interface types (channel /
    # port struct types) unqualified, so re-emit the block's interface-context
    # imports (and their using-directives) in these classic TUs.
    lines = []
    for context in data['includeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            lines.extend(cpp_context_include_lines(prj, data, context, 'include_cppm'))
    return '\n'.join(lines)

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
            case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are init, header")
    elif(args.template == "tbExternal"):
        refactor_tbExternal(args, prj, data)
        match args.section:
            case 'init' : return ext_sec_init(args, prj, data)
            case 'body': return ext_sec_body(args, prj, data)
            case 'header': return ext_sec_header(args, prj, data)
            case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are init, body, header")
    elif(args.template == "tbConfig"):
        return tb_config_class(args, prj, data)
    else:
        raise ValueError(f"Unknown template '{args.template}' for testbench renderer")

def _tb_selection(args, prj, data):
    # Resolve once and reuse across the four testbench/external sections.
    # Reads block view fields populated by getBDConfigInfo (variantConfigs,
    # defaultConfig, isParameterizable). The Testbench/External/Config
    # class-name family is always the plain block name: `--variant` selects
    # only configName and factoryVariant, not emitted file or class names.
    blockName = data['blockName']
    variant = getattr(args, 'variant', None)
    sel = resolve_dut_variant_selection(data, variant)
    hasOwnParams = data['hasOwnParams']
    configName = sel['configName']
    cfg = f'<{configName}>' if hasOwnParams and configName else ''
    return {
        'blockName':      blockName,
        'tbClassName':    blockName,
        'hasOwnParams':   hasOwnParams,
        'configName':     configName,
        'cfg':             cfg,
        'factoryVariant': sel['factoryVariant'],
    }


def tb_config_class(args, prj, data):
    t = Template(sec_tb_config_class_template)
    sel = _tb_selection(args, prj, data)
    s = t.render(blockname=sel['blockName'], tbclassname=sel['tbClassName'],
                 projectname=prj.config.getConfig('PROJECTNAME'))
    return s

def tb_sec_init(args, prj, data):
    t = Template(sec_tb_class_init_template)
    sel = _tb_selection(args, prj, data)
    blockName = sel['blockName']
    instName = blockName
    isParameterizable = data['isParameterizable']
    s = t.render(blockname=blockName, tbclassname=sel['tbClassName'],
                 dutinstname=instName, extinstname="external",
                 is_parameterizable=isParameterizable, cfg=sel['cfg'],
                 default_config=sel['configName'],
                 factory_variant=sel['factoryVariant'],
                 projectname=prj.config.getConfig('PROJECTNAME'))
    return s

def tb_sec_header(args, prj, data):
    t = Template(sec_tb_class_header_template)
    sel = _tb_selection(args, prj, data)
    blockName = sel['blockName']
    instName = blockName
    isParameterizable = data['isParameterizable']
    s = t.render(blockname=blockName, tbclassname=sel['tbClassName'],
                 dutinstname=instName, extinstname="external",
                 is_parameterizable=isParameterizable, cfg=sel['cfg'],
                 default_config=sel['configName'],
                 basemodule=cpp_base_module_name(blockName),
                 context_includes=_tb_context_import_lines(prj, data))
    return s

def ext_sec_init(args, prj, data):

    out = []
    out += sc_instance_includes(data, prj)
    isParameterizable = data['isParameterizable']
    # The External pseudo-block inherits `<DUT>Inverted{cfg}`, which loses its
    # template head when the DUT has no own params. The External class name is
    # the plain `<block>External`; `--variant` selects only the Config and
    # factory variant referenced inside it.
    sel = _tb_selection(args, prj, data)
    # The Inverted base's template argument is the excluded DUT instance's
    # Config when present; otherwise `data` is the DUT block itself.
    cfg = data['dutInvertedCfg'] if data['dutInvertedCfg'] is not None else sel['cfg']

    s = """
{tbClassName}External::{tbClassName}External(sc_module_name modulename) :
    {blockName}Inverted{cfg}("Chnl"),
    log_(name())\n"""
    out.append(s.format(blockName=sel['blockName'], tbClassName=sel['tbClassName'], cfg=cfg))

    for data_ in data['subBlockInstances'].values():
        # Child instance casts target the child's per-variant Config, not the
        # parent's defaultConfig. Empty descriptors fall back to the child's
        # default Config.
        instCfg = cpp_config_arg(data_['instanceConfigSelection'])
        # Generated createInstance passes the variant string and the child's
        # factory-lookup projectName; the factory key is
        # `(blockType, variant, projectName)`. `createInstanceProjectName`
        # (a projectOpen view field) is the assembler for parameterizable and
        # same-project children, and the owning project for a plain
        # cross-project child. Non-templated children self-register via an
        # A2C_REGISTRATION_RETAIN static in their own TU, so the testbench holds
        # no symbol reference to them.
        projectName = data_['createInstanceProjectName']
        createCall = (
            'instanceFactory::createInstance(name(), "{instName}", '
            '"{blockName}", "{variant}", "{projectName}")'
        )
        s = '   ,{instName}(std::dynamic_pointer_cast<{blockName}Base{instCfg}>(' + createCall + '))'
        out.append(s.format(blockName=data_['instanceType'], instName=data_['instance'], instCfg=instCfg, variant=data_.get('variant', ''), projectName=projectName))

    for channelType in data['connectDouble']:
        for connKey,data_ in data['connectDouble'][channelType].items():
            srcInstances = [v.get('instance') for v in data_['ends'].values() if v.get('direction') == "src"]
            if len(srcInstances) != 1:
                printError(f"Expected exactly one src instance for connection {connKey!r} ({channelType}), found {len(srcInstances)}")
                exit(warningAndErrorReport())
            srcInst = srcInstances[0]
            chnlData = sc_gen_block_channels(data_, prj, data)
            s = '   ,{chnlName}("{chnlName}", "{instName}")'
            out.append(s.format(chnlName=chnlData['chnl_name'], instName=srcInst))
            # Mirror the DUT's cross-interface thunker emission inside the
            # external pseudo-block. Without these entries the consumer-side
            # port whose interface is bridged by a thunker in the DUT would
            # remain unbound during external elaboration.
            for flagged in _resolve_cross_interface_ends(data_, prj):
                memberName = _thunker_member_name(flagged, data_, is_connection_map=False)
                out.append(
                    f'   ,{memberName}("{memberName}", {chnlData["chnl_name"]}, '
                    f'{flagged["instance"]}->{flagged["portName"]}, name())'
                )

    # Emit a local-only channel for each connectionMap port carried by a
    # contained instance. The external pseudo-block inherits ip_topInverted's
    # parent port for the same interface, but the inverted direction means it
    # cannot serve as the binding target for the contained instance's port.
    # The local channel satisfies SC port binding without disturbing the
    # testbench harness's parent-port wiring.
    for key, value in data.get('connectionMaps', dict()).items():
        if _resolve_cross_interface_ends(value, prj):
            continue
        instName = value.get('instance', '')
        instPort = value.get('instancePortName', '')
        out.append(
            f'   ,_ext_cm_{instName}_{instPort}('
            f'"_ext_cm_{instName}_{instPort}", "{instName}")'
        )

    # DUT-boundary thunkers: for each connection pruned to the excluded DUT
    # instance whose surviving end is a cross-interface bind, construct the
    # thunker adapting the contained instance's port to the inherited
    # <DUT>Inverted boundary port (the same port the raw prunedConnections bind
    # would target). Constructing the thunker performs the bind, so ext_sec_body
    # suppresses the raw bind for these ends. The <proto>_port_thunker overload
    # resolves by port direction: consumer surviving end -> connectionMap shape,
    # producer surviving end -> producer-port shape.
    for key, value in data.get('prunedConnections', dict()).items():
        for end, endvalue in value['ends'].items():
            flagged = endvalue.get('crossInterface')
            if not flagged:
                continue
            boundaryPort = getPortChannelName(value, inverse_portdir(endvalue['direction']) + 'port')
            memberName = _thunker_member_name(flagged, value, is_connection_map=False)
            out.append(
                f'   ,{memberName}("{memberName}", {boundaryPort}, '
                f'{flagged["instance"]}->{flagged["portName"]}, name())'
            )

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
            multiDst = get_intf_defs(get_intf_type(value['interfaceType'], data), data).get('multiDst', False)
            if not multiDst:
                printError(f"connection {key} has more than 2 ends. Only status interfaces (including ro registers) can have multiple dst connections")
        for end, endvalue in value["ends"].items():
            # Cross-interface ends are bound through a thunker constructed in
            # ext_sec_init; emitting the raw bind here too would double-bind
            # (and would not type-check across the differing interfaces).
            if 'crossInterface' in endvalue:
                continue
            port_name = getPortChannelName(value, inverse_portdir(endvalue['direction']) + 'port')
            port_names.add(port_name)
            prunedConnections.append(f'{indent}{ endvalue["instance"] }->{ endvalue["portName"]}({ port_name });')

    # resolve any port-channel name clashes
    for conn, conn_data in data.get('connections', dict()).items():
        if conn_data['interfaceName'] in port_names:
            conn_data['interfaceName'] = conn_data['interfaceName'] + '_'

    # channels outside of any that include the excluded instances
    connections = sc_connect_channels(data, indent, data)

    # Bind the contained instance's connectionMap port to the local-only
    # channel declared in ext_sec_header.
    cm_binds = []
    for key, value in data.get('connectionMaps', dict()).items():
        if _resolve_cross_interface_ends(value, prj):
            continue
        instName = value.get('instance', '')
        instPort = value.get('instancePortName', '')
        memberName = f'_ext_cm_{instName}_{instPort}'
        cm_binds.append(f'{indent}{instName}->{instPort}({memberName});')

    if connections or prunedConnections or cm_binds:
        out.append(indent +'// instance to instance connections via channel')
        out += connections
        out += prunedConnections
        out += cm_binds

    out.append('\n' + indent +'SC_THREAD(eotThread);')

    return "\n".join(out)

def ext_sec_header(args, prj, data):

    ext_fwd_decl_s = []
    external_blocks = sorted(data['subBlocks'].values())
    isParameterizable = data['isParameterizable']
    # External pseudo-block inherits `<DUT>Inverted{cfg}`. The External class
    # name stays on the plain TB-family stub; only the selected Config suffix
    # changes when the file-level GENERATED_CODE_PARAM names a different DUT
    # variant.
    sel = _tb_selection(args, prj, data)
    hasOwnParams = sel['hasOwnParams']
    defaultConfig = sel['configName']
    # The Inverted base's template argument is the excluded DUT instance's
    # Config when present; otherwise `data` is the DUT block itself.
    cfg = data['dutInvertedCfg'] if data['dutInvertedCfg'] is not None else sel['cfg']
    # A non-parameterizable child's Base is a plain class: a global-module
    # forward declaration merges with the module's exported class, so
    # forward-declaring keeps the header light. A parameterizable child's Base
    # is a class template; a global-module forward declaration would be a
    # DISTINCT entity from the module's exported template, so the member type
    # and the createInstance dynamic_pointer_cast target would carry mismatched
    # RTTI and the cast would return null. Import the child's Base module
    # instead so the member type is the real module type (mirrors the DUT's own
    # <DUT>Testbench importing <DUT>.base).
    ext_child_base_imports_s = []
    for blockKey, blockName in sorted(data['subBlocks'].items(), key=lambda item: item[1]):
        childHasOwnParams = data['subBlockTypes'][blockKey]['hasOwnParams']
        if childHasOwnParams:
            ext_child_base_imports_s.append(f'import {cpp_base_module_name(blockName)};')
        else:
            ext_fwd_decl_s.append(f'class {blockName}Base;')

    ext_inst_decl_s = []
    external_insts = [v for v in data['subBlockInstances'].values() ]
    for data_ in external_insts:
        # Per-instance Config for parameterizable children.
        instCfg = cpp_config_arg(data_['instanceConfigSelection'])
        ext_inst_decl_s.append(f'std::shared_ptr<{data_["instanceType"]}Base{instCfg}> {data_["instance"]};')

    # Channel types derive from the connected child's per-variant Config
    # inside sc_gen_block_channels' connection-walk. The post-hoc
    # `replace('<Config>', f'<{defaultConfig}>')` substitution that previously
    # mapped the parent's template parameter onto the parent's defaultConfig is
    # therefore obsolete for the typical case. We retain the substitution as a
    # fallback for channels whose endpoints are not parameterizable child
    # instances but still reference parameterizable structures; those parents
    # are non-templated and the literal `<Config>` would otherwise leak through
    # as an undeclared name.
    ext_chnl_decl_s = sc_declare_channels(data, prj, ' '*4, data)
    if isParameterizable:
        ext_chnl_decl_s = [line.replace('<Config>', f'<{defaultConfig}>') for line in ext_chnl_decl_s]

    # Declare local-only channels for connectionMap ports on contained
    # instances. See ext_sec_init for the matching member-init and
    # ext_sec_body for the bind to the contained instance.
    for key, value in data.get('connectionMaps', dict()).items():
        if _resolve_cross_interface_ends(value, prj):
            continue
        instName = value.get('instance', '')
        instPort = value.get('instancePortName', '')
        intfInfo = prj.data['interfaces'].get(value.get('interfaceKey', ''))
        if not intfInfo:
            continue
        synth_conn = dict(value)
        synth_conn['interfaceType'] = intfInfo['interfaceType']
        synth_conn['interfaceName'] = intfInfo['interface']
        synth_conn['maxTransferSize'] = intfInfo.get('maxTransferSize', '0')
        # Neutral Config selection of the contained instance whose port this
        # local-only channel serves; sc_gen_block_channels spells the struct
        # name. None when the instance is absent or not parameterizable.
        synth_conn['configOverride'] = (
            data.get('subBlockInstances', {})
                .get(value.get('instanceKey', ''), {})
                .get('instanceConfigSelection')
        )
        chnlData = sc_gen_block_channels(synth_conn, prj, data)
        chnl_decl = chnlData["channel_decl"]
        # channel_decl is "<type><params> <name>;"; replace the
        # auto-derived name with the local-only name.
        memberName = f'_ext_cm_{instName}_{instPort}'
        local_decl = chnl_decl.rsplit(' ', 1)[0] + f' {memberName};'
        ext_chnl_decl_s.append(f'    {local_decl}')

    # When the DUT contains cross-interface thunker members, the external
    # pseudo-block must mirror them so its consumer-side ports complete binding
    # during elaboration. The decls and matching header include remain off
    # when no cross-interface ends are flagged.
    ext_thunker_decl_s = sc_declare_thunkers(data, prj, ' '*4, data)
    thunker_includes = sorted(sc_thunker_protocols(data, prj))
    thunker_include_lines = [f'#include "{proto}_port_thunker.h"' for proto in thunker_includes]

    # Channel headers for the interface types the External's declared channels
    # use, via the shared sc_channel_header_includes helper (same emission as the
    # block implementations): a tb External declares DUT-boundary channel members
    # directly, so it needs each channel's header (which also carries the payload
    # structs). The filters match the channels sc_declare_channels emits (non-skip)
    # and the local connectionMap channels (non cross-interface; cross-interface
    # maps use thunkers instead).
    intf_types = set()
    for conns in data['connectDouble'].values():
        for value in conns.values():
            if not sc_gen_block_channels(value, prj, data)['is_skip']:
                intf_types.add(get_intf_type(value['interfaceType'], data))
    for value in data.get('connectionMaps', dict()).values():
        if _resolve_cross_interface_ends(value, prj):
            continue
        intfInfo = prj.data['interfaces'].get(value.get('interfaceKey', ''))
        if intfInfo:
            intf_types.add(get_intf_type(intfInfo['interfaceType'], data))
    channel_include_lines = sc_channel_header_includes(intf_types, data)

    t = Template(sec_tb_external_header_template)
    config_includes = []
    for context in sorted(data.get('configIncludeContext', {})):
        if context in data['includeFiles'].get('config_hdr', {}):
            config_includes.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')
    s = t.render(
        blockname=data['blockName'],
        basemodule=cpp_base_module_name(data['blockName']),
        context_includes=_tb_context_import_lines(prj, data),
        tbclassname=sel['tbClassName'],
        is_parameterizable=isParameterizable,
        cfg=cfg,
        default_config=defaultConfig,
        config_includes='\n'.join(config_includes),
        channel_includes='\n'.join(channel_include_lines),
        thunker_includes='\n'.join(thunker_include_lines),
        child_base_imports='\n'.join(ext_child_base_imports_s),
        ext_fwd_decl='\n'.join(ext_fwd_decl_s),
        ext_inst_decl='\n'.join(ext_inst_decl_s),
        ext_chnl_decl='\n'.join(ext_chnl_decl_s),
        ext_thunker_decl='\n'.join(ext_thunker_decl_s)
    )
    return(s)

"""
Refactor the external block connectivity to be used in the testbench
and avoid channel name clashes
"""
def refactor_tbExternal(args, prj, data):
    if len(data['excludedInstances']) > 0:
        dutInst = data['excludedInstances'][next(iter(data['excludedInstances']))]
        blockname = dutInst['instanceType']
        # The External pseudo-block inherits `<DUT>Inverted<Config>`. When the
        # DUT is an excluded instance of a separate testbench-top block, the
        # template argument is that instance's Config, not the (possibly
        # param-less) testbench-top block's cfg from _tb_selection.
        data['dutInvertedCfg'] = cpp_config_arg(dutInst['instanceConfigSelection'])
    else:
        # No excluded instance: `data` already is the DUT block, so the
        # Inverted base cfg comes from _tb_selection (sentinel None).
        blockname = data['blockName']
        data['dutInvertedCfg'] = None
    data['blockName'] = blockname

sec_tb_class_header_template = """\
#include "systemc.h"
#include "instanceFactory.h"

import {{basemodule}};
{%- if context_includes %}
{{context_includes}}
{%- endif %}
#include "{{tbclassname}}External.h"

class {{tbclassname}}Testbench: public sc_module, public blockBase, public {{blockname}}Channels{{cfg}} {

public:

    std::shared_ptr<{{blockname}}Base{{cfg}}> {{dutinstname}};
    {{tbclassname}}External {{extinstname}};

    {{tbclassname}}Testbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~{{tbclassname}}Testbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
"""

sec_tb_class_init_template = """\
#include "{{tbclassname}}Testbench.h"

// === Block factory registration ({{tbclassname}}Testbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_{{tbclassname}}Testbench_variants() {
    instanceFactory::registerBlock("{{tbclassname}}Testbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{{tbclassname}}Testbench>(blockName, variant, bbMode)); }, "", "{{projectname}}");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _{{tbclassname}}Testbench_registered = (register_{{tbclassname}}Testbench_variants(), 0);
} // namespace
// === End block factory registration ===

{{tbclassname}}Testbench::{{tbclassname}}Testbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("{{tbclassname}}Testbench", name(), bbMode)
        ,{{blockname}}Channels{{cfg}}("Chnl", "tb")
        ,{{dutinstname}}(std::dynamic_pointer_cast<{{blockname}}Base{{cfg}}>( instanceFactory::createInstance(name(), "{{dutinstname}}", "{{blockname}}", "{{factory_variant}}", "{{projectname}}")))
        ,{{extinstname}}("{{extinstname}}")
{
    bind({{dutinstname}}.get(), &{{extinstname}});
}
"""

sec_tb_external_header_template = """\

#include "instanceFactory.h"
import {{basemodule}};
{%- if child_base_imports %}
{{child_base_imports}}
{%- endif %}
{%- if channel_includes %}
{{channel_includes}}
{%- endif %}
{%- if context_includes %}
{{context_includes}}
{%- endif %}
{%- if config_includes %}
{{config_includes}}
{%- endif %}
{%- if thunker_includes %}
{{thunker_includes}}
{%- endif %}
#include "endOfTest.h"

{%- if ext_fwd_decl %}

//contained instances forward class declaration
{{ext_fwd_decl}}
{%- endif %}

class {{tbclassname}}External: public sc_module, public {{blockname}}Inverted{{cfg}} {

    logBlock log_;

public:

{%- if ext_inst_decl %}

    {{ ext_inst_decl | indent(4) }}
{%- endif %}

    SC_HAS_PROCESS ({{tbclassname}}External);

    {{tbclassname}}External(sc_module_name modulename);

{%- if ext_chnl_decl %}

{{ ext_chnl_decl }}
{%- endif %}
{%- if ext_thunker_decl %}

    // cross-interface thunkers
{{ ext_thunker_decl }}
{%- endif %}

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

"""

sec_tb_config_class_template = """\

class {{tbclassname}}Config : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("{{tbclassname}}", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<{{tbclassname}}Config>());}, is_default_testbench_v<{{tbclassname}}Config>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~{{tbclassname}}Config() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "{{tbclassname}}Testbench", "", "{{projectname}}"); }
public:
"""
