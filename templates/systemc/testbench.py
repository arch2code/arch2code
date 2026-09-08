
import textwrap

from pysrc.processYaml import getPortChannelName
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.intf_gen_utils import sc_gen_block_channels, sc_connect_channels, sc_instance_includes, sc_declare_channels, get_intf_type, get_intf_defs, inverse_portdir, resolve_dut_variant_selection, sc_declare_thunkers, sc_thunker_protocols, _resolve_cross_interface_ends, _thunker_member_name, cpp_base_module_name, cpp_tb_module_name, cpp_tb_external_module_name, cpp_context_include_lines, cpp_config_arg, cpp_own_config_import, sc_channel_header_includes, cpp_container_typed_instance_arg, sc_instance_config_imports, BLOCK_CONFIG_PARAM

from jinja2 import Template


def _tb_context_lines(prj, data):
    # A module import does not propagate the base module's own context imports /
    # using-directives. The testbench top and its External pseudo-block spell the
    # DUT's interface types (channel / port struct types) unqualified, so both
    # re-state the block's interface-context imports and using-directives.
    lines = []
    for context in data['includeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            lines.extend(cpp_context_include_lines(prj, context))
    return lines


def _tb_context_imports(prj, data):
    # Interface-context `import` lines - module preamble only (moduleExport).
    return [line for line in _tb_context_lines(prj, data)
            if not line.startswith('using namespace ')]


def _tb_context_usings(prj, data):
    # Interface-context `using namespace` lines. A using-directive CLOSES the
    # module preamble, so these ride at the head of the class region (module
    # purview) instead, leaving the sibling `// user imports here` slot a legal
    # place for a hand-authored import. Mirrors classDecl in module mode.
    return [line for line in _tb_context_lines(prj, data)
            if line.startswith('using namespace ')]


def _ext_holds_peers(data):
    # excludeInst shape: the External holds the DUT's peer blocks and the wiring
    # between them. In block mode the target block IS the DUT and instantiates
    # its own children in its own generated region, so the External emits no
    # instance members, channels, thunkers or connectionMap locals and all
    # stimulus is hand-written in its user region.
    return bool(data['excludedInstances'])


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
        match args.section:
            case 'prerequisites': return tb_config_prerequisites(args, prj, data)
            case 'class': return tb_config_class(args, prj, data)
            case 'registration': return tb_config_registration(args, prj, data)
            case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are prerequisites, class, registration")
    else:
        raise ValueError(f"Unknown template '{args.template}' for testbench renderer")

def _tb_selection(args, prj, data):
    # Resolve once and reuse across the four testbench/external sections. The
    # Testbench/External/Config class-name family is always the plain block name:
    # `--variant` selects only configName and factoryVariant, not emitted file or
    # class names.
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


def _tb_bind_container_config(text, data, sel):
    # Bind the container's class template parameter to its own resolved Config
    # across one rendered External region. Per-instance spellings that defer to
    # the container (inheritContainerParam, a container-sourced variant's Config
    # template, a nested-Config alias) name that parameter, which is declared in
    # the container's class template but not in the External - the one consumer
    # of the per-instance Config machinery that is not itself a class template.
    # A non-parameterizable container emits no such spelling.
    if not data['isParameterizable']:
        return text
    return text.replace(f'<{BLOCK_CONFIG_PARAM}>', f'<{sel["configName"]}>')


def tb_config_prerequisites(args, prj, data):
    # a2c.endOfTest and the DUT's own Config module back the user-owned final()
    # and createTestBench() bodies, not the generated lines.
    out = [
        '#include <string>',
        '#include "instanceFactory.h"',
        '#include "testBenchConfigFactory.h"',
    ]
    out.extend(cpp_own_config_import(data))
    out.append('import a2c.endOfTest;')
    return "\n".join(out)


def tb_config_class(args, prj, data):
    t = Template(sec_tb_config_class_template)
    sel = _tb_selection(args, prj, data)
    s = t.render(blockname=sel['blockName'], tbclassname=sel['tbClassName'],
                 projectname=prj.config.getConfig('PROJECTNAME'))
    return s


def tb_config_registration(args, prj, data):
    # Factory registration for the Config class, emitted after the class closes so
    # `is_default_testbench_v` sees the complete type (including a user-supplied
    # isDefaultTestBench marker).
    t = Template(sec_tb_config_registration_template)
    sel = _tb_selection(args, prj, data)
    return t.render(tbclassname=sel['tbClassName'])

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
    # The testbench top class IS exported from `<block>.testbench`, and must stay so
    # even though NO GENERATED FILE imports that module - the factory path
    # (createTbTop in the tbConfig class region) constructs the top, it does not name
    # the type. A `<block>Config.cpp` commonly does
    # `dynamic_cast<<block>Testbench *>(tb.get())` and then reaches
    # `tb_ptr->external.<member>` to configure sub-instances before simulation starts;
    # an unexported class in a module purview cannot be named by an importer at all,
    # so dropping the export makes that whole pattern a hard error.
    t = Template(sec_tb_class_header_template)
    sel = _tb_selection(args, prj, data)
    blockName = sel['blockName']
    instName = blockName
    isParameterizable = data['isParameterizable']
    s = t.render(blockname=blockName, tbclassname=sel['tbClassName'],
                 dutinstname=instName, extinstname="external",
                 is_parameterizable=isParameterizable, cfg=sel['cfg'],
                 default_config=sel['configName'],
                 context_usings='\n'.join(_tb_context_usings(prj, data)))
    return s

def _ext_channel_includes(prj, data):
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
    for value in data['connectionMaps'].values():
        if _resolve_cross_interface_ends(value, prj):
            continue
        intfInfo = prj.data['interfaces'][value['interfaceKey']]
        intf_types.add(get_intf_type(intfInfo['interfaceType'], data))
    return sc_channel_header_includes(intf_types, data)


def ext_module_header(args, prj, data):
    # Global module fragment for `<block>External.cppm`; the export decl and
    # every import live in the sibling `moduleExport --fileMapKey=tbExternal`
    # region.
    refactor_tbExternal(args, prj, data)
    holdsPeers = _ext_holds_peers(data)
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "logging.h"',
        '#include "instanceFactory.h"',
    ]
    if holdsPeers:
        out += _ext_channel_includes(prj, data)
    if holdsPeers:
        for proto in sorted(sc_thunker_protocols(data, prj)):
            out.append(f'#include "{proto}_port_thunker.h"')
    return "\n".join(out)


def ext_module_export(args, prj, data):
    # The COMPLETE module preamble for `<block>External.cppm`. Every import must
    # precede the first non-import declaration, and a using-directive closes the
    # preamble, so this region is import-only and the context using-directives ride
    # at the head of the class region instead (see _tb_context_usings).
    # a2c.endOfTest is imported here so the
    # in-class eotThread() body resolves endOfTestState with no prerequisite leaked
    # to consumers. Every contained instance's Base is imported unconditionally: a
    # forward declaration in a module purview is a DISTINCT entity from the child's
    # exported class, so the shared_ptr member type and the createInstance
    # dynamic_pointer_cast target would carry mismatched RTTI and the cast would
    # silently return null. Both child-facing import sets belong to the External's
    # OWN contents and so are excludeInst-mode only.
    refactor_tbExternal(args, prj, data)
    out = [f'export module {cpp_tb_external_module_name(data["blockModuleName"])};']
    out.append('import a2c.endOfTest;')
    out.append(f'import {cpp_base_module_name(data["blockModuleName"])};')
    out += cpp_own_config_import(data)
    if _ext_holds_peers(data):
        out += sc_instance_includes(data, prj)
        out += sc_instance_config_imports(data)
    out += _tb_context_imports(prj, data)
    return "\n".join(out)


def tb_module_header(args, prj, data):
    # Global module fragment for `<block>Testbench.cppm`; imports live in the
    # sibling `moduleExport --fileMapKey=testBench` region.
    out = [
        'module;',
        '#include "systemc.h"',
        '#include "instanceFactory.h"',
    ]
    return "\n".join(out)


def tb_module_export(args, prj, data):
    # Import-only preamble, same reason as ext_module_export. No a2c.endOfTest
    # import here; eotThread lives in the External module.
    out = [f'export module {cpp_tb_module_name(data["blockModuleName"])};']
    out.append(f'import {cpp_base_module_name(data["blockModuleName"])};')
    out.append(f'import {cpp_tb_external_module_name(data["blockModuleName"])};')
    out += cpp_own_config_import(data)
    out += _tb_context_imports(prj, data)
    return "\n".join(out)


def ext_sec_init(args, prj, data):

    out = []
    isParameterizable = data['isParameterizable']
    sel = _tb_selection(args, prj, data)
    # The Inverted base's template argument is the excluded DUT instance's
    # Config when present; otherwise `data` is the DUT block itself.
    cfg = data['dutInvertedCfg'] if data['dutInvertedCfg'] is not None else sel['cfg']

    s = """
{tbClassName}External::{tbClassName}External(sc_module_name modulename) :
    {blockName}Inverted{cfg}("Chnl"),
    log_(name())\n"""
    out.append(s.format(blockName=sel['blockName'], tbClassName=sel['tbClassName'], cfg=cfg))

    if _ext_holds_peers(data):
        for data_ in data['subBlockInstances'].values():
            # Child instance casts target the child's per-variant Config, not the
            # parent's defaultConfig. Empty descriptors fall back to the child's
            # default Config.
            instCfg = cpp_config_arg(data_['instanceConfigSelection'])
            # `createInstanceProjectName` (a projectOpen view field) is the
            # assembler for parameterizable and same-project children, and the
            # owning project for a plain cross-project child. Non-templated children
            # self-register in their own TU, so the testbench holds no symbol
            # reference to them.
            projectName = data_['createInstanceProjectName']
            # A child typed by the container's Config: no registration can name its
            # class, so the class is named as an explicit template argument of
            # createInstance.
            implArg = cpp_container_typed_instance_arg(data_)
            createCall = (
                'instanceFactory::createInstance{implArg}(name(), "{instName}", '
                '"{blockName}", "{variant}", "{projectName}")'
            )
            s = '   ,{instName}(std::dynamic_pointer_cast<{blockName}Base{instCfg}>(' + createCall + '))'
            out.append(s.format(blockName=data_['instanceType'], instName=data_['instance'], instCfg=instCfg, variant=data_['variant'], projectName=projectName, implArg=implArg))

        for channelType in data['connectDouble']:
            for connKey,data_ in data['connectDouble'][channelType].items():
                srcInstances = [v['instance'] for v in data_['ends'].values() if v['direction'] == "src"]
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
        for key, value in data['connectionMaps'].items():
            if _resolve_cross_interface_ends(value, prj):
                continue
            instName = value['instance']
            instPort = value['instancePortName']
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
    for key, value in data['prunedConnections'].items():
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

    return _tb_bind_container_config("\n".join(out), data, sel)

def ext_sec_body(args, prj, data):

    out = []

    indent = ' '*4

    out.append('{')
    prunedConnections = []
    port_names = set()
    # connect hierarchical ports that connect the excluded instances to the external blocks
    for key, value in data['prunedConnections'].items():
        if (len(value['ends']) > 2):
            multiDst = get_intf_defs(get_intf_type(value['interfaceType'], data), data)['multiDst']
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
    for conn, conn_data in data['connections'].items():
        if conn_data['interfaceName'] in port_names:
            conn_data['interfaceName'] = conn_data['interfaceName'] + '_'

    connections = []
    cm_binds = []
    if _ext_holds_peers(data):
        # channels outside of any that include the excluded instances
        connections = sc_connect_channels(data, indent, data)

        # Bind the contained instance's connectionMap port to the local-only
        # channel declared in ext_sec_header.
        for key, value in data['connectionMaps'].items():
            if _resolve_cross_interface_ends(value, prj):
                continue
            instName = value['instance']
            instPort = value['instancePortName']
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

    # The External class only. Every #include lives in the sibling global module
    # fragment (moduleScaffold --section=tbExternalModuleHeader) and every import in
    # the sibling moduleExport region; the only dependency lines emitted here are the
    # interface-context using-directives, at the region head, because a
    # using-directive closes the module preamble and would otherwise make the
    # `// user imports here` slot above unusable for a hand-authored import.
    sel = _tb_selection(args, prj, data)
    # The Inverted base's template argument is the excluded DUT instance's
    # Config when present; otherwise `data` is the DUT block itself.
    cfg = data['dutInvertedCfg'] if data['dutInvertedCfg'] is not None else sel['cfg']

    ext_inst_decl_s = []
    ext_chnl_decl_s = []
    ext_thunker_decl_s = []
    if _ext_holds_peers(data):
        for data_ in data['subBlockInstances'].values():
            # Per-instance Config for parameterizable children.
            instCfg = cpp_config_arg(data_['instanceConfigSelection'])
            ext_inst_decl_s.append(f'std::shared_ptr<{data_["instanceType"]}Base{instCfg}> {data_["instance"]};')

        # Channel types derive from the connected child's per-variant Config
        # inside sc_gen_block_channels' connection-walk. A channel whose endpoints
        # are not parameterizable child instances but which still references
        # parameterizable structures is typed by the container's own template
        # parameter instead; _tb_bind_container_config binds it below, along with
        # every other site of this region.
        ext_chnl_decl_s = sc_declare_channels(data, prj, ' '*4, data)

        # Declare local-only channels for connectionMap ports on contained
        # instances. See ext_sec_init for the matching member-init and
        # ext_sec_body for the bind to the contained instance.
        for key, value in data['connectionMaps'].items():
            if _resolve_cross_interface_ends(value, prj):
                continue
            instName = value['instance']
            instPort = value['instancePortName']
            intfInfo = prj.data['interfaces'][value['interfaceKey']]
            synth_conn = dict(value)
            synth_conn['interfaceType'] = intfInfo['interfaceType']
            synth_conn['interfaceName'] = intfInfo['interface']
            synth_conn['maxTransferSize'] = intfInfo['maxTransferSize']
            # Neutral Config selection of the contained instance whose port this
            # local-only channel serves; sc_gen_block_channels spells the struct
            # name. getBDConnectionMaps admits a row only when its instanceKey is a
            # contained instance, so the instance row is always present here.
            synth_conn['configOverride'] = (
                data['subBlockInstances'][value['instanceKey']]['instanceConfigSelection']
            )
            chnlData = sc_gen_block_channels(synth_conn, prj, data)
            chnl_decl = chnlData["channel_decl"]
            # channel_decl is "<type><params> <name>;"; replace the
            # auto-derived name with the local-only name.
            memberName = f'_ext_cm_{instName}_{instPort}'
            local_decl = chnl_decl.rsplit(' ', 1)[0] + f' {memberName};'
            ext_chnl_decl_s.append(f'    {local_decl}')

        # When the container adapts cross-interface binds, the external
        # pseudo-block must mirror those thunkers so its consumer-side ports
        # complete binding during elaboration.
        ext_thunker_decl_s = sc_declare_thunkers(data, prj, ' '*4, data)

    t = Template(sec_tb_external_header_template)
    s = t.render(
        blockname=data['blockName'],
        context_usings='\n'.join(_tb_context_usings(prj, data)),
        tbclassname=sel['tbClassName'],
        cfg=cfg,
        ext_inst_decl='\n'.join(ext_inst_decl_s),
        ext_chnl_decl='\n'.join(ext_chnl_decl_s),
        ext_thunker_decl='\n'.join(ext_thunker_decl_s)
    )
    return _tb_bind_container_config(s, data, sel)

"""
Refactor the external block connectivity to be used in the testbench
and avoid channel name clashes
"""
def refactor_tbExternal(args, prj, data):
    if _ext_holds_peers(data):
        dutInst = data['excludedInstances'][next(iter(data['excludedInstances']))]
        blockname = dutInst['instanceType']
        # The External pseudo-block inherits `<DUT>Inverted<Config>`. When the
        # DUT is an excluded instance of a separate testbench-top block, the
        # template argument is that instance's Config, not the (possibly
        # param-less) testbench-top block's cfg from _tb_selection.
        data['dutInvertedCfg'] = cpp_config_arg(dutInst['instanceConfigSelection'])
        # The External's `<DUT>.base` import must match the DUT's own qualified
        # export, which is the excluded instance's block, not the testbench-top.
        blockModuleName = dutInst['instanceTypeModuleName']
    else:
        # No excluded instance: `data` already is the DUT block, so the
        # Inverted base cfg comes from _tb_selection (sentinel None).
        blockname = data['blockName']
        data['dutInvertedCfg'] = None
        blockModuleName = data['blockModuleName']
    data['blockName'] = blockname
    data['blockModuleName'] = blockModuleName

sec_tb_class_header_template = """\
{%- if context_usings %}
{{context_usings}}
{%- endif %}

export class {{tbclassname}}Testbench: public sc_module, public blockBase, public {{blockname}}Channels{{cfg}} {

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
{%- if context_usings %}
{{context_usings}}
{%- endif %}

export class {{tbclassname}}External: public sc_module, public {{blockname}}Inverted{{cfg}} {

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
    virtual ~{{tbclassname}}Config() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
protected:
    // The testbench top is instantiated through this generated helper so its
    // factory-key projectName is emitted here on every make gen (matching the
    // tb-top registration), instead of being hand-written into the user body.
    std::shared_ptr<blockBase> createTbTop(void) { return instanceFactory::createInstance("", "tb", "{{tbclassname}}Testbench", "", "{{projectname}}"); }
public:
"""

sec_tb_config_registration_template = """\
// === Testbench config registration ({{tbclassname}}Config) ===
// The config self-registers through an A2C_REGISTRATION_RETAIN static (see
// instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference. Emitted after the class closes so is_default_testbench_v
// sees a complete type, including a user-supplied isDefaultTestBench marker.
void register_{{tbclassname}}Config() {
    testBenchConfigFactory::registerTestBenchConfig("{{tbclassname}}", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<{{tbclassname}}Config>());}, is_default_testbench_v<{{tbclassname}}Config>);
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _{{tbclassname}}Config_registered = (register_{{tbclassname}}Config(), 0);
} // namespace
// === End testbench config registration ==="""
