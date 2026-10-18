# The factory registration of a hasUvm block's UVM testbench wrapper, one per
# standalone variant (one variantless registration for a block without
# params), each over that variant's simulator shell and Config. The key is
# (<block>_uvm, variant, project), which the generated UVM config selects with
# registerInstance("<block>", "uvm"). Only the Xcelium and VCS builds compile
# it, because only they write the shells.
from pysrc.intf_gen_utils import resolve_dut_variant_selection
from templates.systemc.blockRegistrar import emit_register_call


def render(args, prj, data):
    uvm = data['uvm']
    blockName = data['blockName']
    project = prj.config.getConfig('PROJECTNAME')
    tops = uvm['tops']
    out = ['#if defined(XCELIUM) || defined(VCS)',
           '#include "instanceFactory.h"',
           '#include "blockBase.h"',
           f'#include "{uvm["scWrapperHeader"]}"',
           '#if defined(XCELIUM)']
    out += [f'#include "{top["xceliumShellHeader"]}"' for top in tops.values()]
    out.append('#else')
    out.append('// Written by vlogan -sc_model from the port map.')
    out += [f'#include "{top["vcsShellHeader"]}"' for top in tops.values()]
    out.append('#endif')

    registrations = list()
    for variant, top in tops.items():
        config = resolve_dut_variant_selection(data, variant or None)['configName']
        templateArgs = f"{top['tbModule']}, {config}" if data['hasOwnParams'] else top['tbModule']
        registrations += emit_register_call(
            suffix='uvm',
            blockName=blockName,
            targetClass=f"{uvm['scWrapperClass']}<{templateArgs}>",
            variant=variant,
            projectName=project,
            indent='        ')
    out += ['',
            'namespace {',
            f'struct _{blockName}_uvm_registrar {{',
            f'    _{blockName}_uvm_registrar() {{',
            *registrations,
            '    }',
            '};',
            f'static _{blockName}_uvm_registrar _{blockName}_uvm_registrar_instance;',
            '} // namespace',
            '#endif // XCELIUM || VCS']
    return '\n'.join(out) + '\n'
