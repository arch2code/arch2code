# The UVM testbench config of a hasUvm block at the variant its
# GENERATED_CODE_PARAM line names. It creates the SystemC wrapper through the
# instanceFactory under the block's own name, with the DUT --uvmDut picks,
# and fails the run in final() unless UVM finished with no error. Only the
# Xcelium and VCS builds compile it: the wrapper's shell exists only there.
from pysrc.intf_gen_utils import resolve_dut_variant_selection


def render(args, prj, data):
    uvm = data['uvm']
    blockName = data['blockName']
    run = uvm['runClass']
    variant = resolve_dut_variant_selection(data, args.variant)['factoryVariant']
    project = prj.config.getConfig('PROJECTNAME')
    if data['blockInfo']['hasMdl']:
        dutCheck = [
            '        if (m_uvmDut != "model" && m_uvmDut != "rtl") {',
            '            std::cerr << "--uvmDut must be model or rtl, not " << m_uvmDut << std::endl;',
            '            return false;',
            '        }',
        ]
        defaultDut = 'model'
        dutHelp = 'DUT behind the UVM testbench: model or rtl; must match the snapshot'
    else:
        dutCheck = [
            '        if (m_uvmDut != "rtl") {',
            f'            std::cerr << "--uvmDut must be rtl, because {blockName} has no model, not " << m_uvmDut << std::endl;',
            '            return false;',
            '        }',
        ]
        defaultDut = 'rtl'
        dutHelp = f'DUT behind the UVM testbench: rtl, because {blockName} has no model'
    out = [
        '#if defined(XCELIUM) || defined(VCS)',
        '#include <iostream>',
        '#include <memory>',
        '#include <string>',
        '#include "instanceFactory.h"',
        '#include "testBenchConfigFactory.h"',
        f'#include "{uvm["scWrapperHeader"]}"',
        '',
        'namespace {',
        '',
        'class uvmTbConfig : public testBenchConfigBase',
        '{',
        'public:',
        '    void addProgramOptions(po::options_description &options) override',
        '    {',
        '        options.add_options()',
        f'        ("uvmDut", po::value<std::string>(&m_uvmDut)->default_value("{defaultDut}"), "{dutHelp}");',
        '    }',
        '',
        '    bool handleProgramOptions(po::variables_map &vm) override',
        '    {',
        *dutCheck,
        '        return true;',
        '    }',
        '',
        '    // No firmware worker threads: the UVM register model programs the block.',
        '    bool createTestBench(void) override',
        '    {',
        f'        {run}::rtlDut = m_uvmDut == "rtl";',
        f'        instanceFactory::registerInstance("{blockName}", "uvm");',
        f'        instanceFactory::createInstance("", "{blockName}", "{blockName}", "{variant}", "{project}");',
        '        return true;',
        '    }',
        '',
        '    // try_sc_start overwrites the error string after the run, so the failure',
        '    // recorded during the run is set again here for the exit summary.',
        '    void final(void) override',
        '    {',
        f'        if (!{run}::completed) {{',
        f'            errorCode::fail({run}::notFinished);',
        f'        }} else if (!{run}::failure.empty()) {{',
        f'            errorCode::fail({run}::failure);',
        '        } else {',
        '            errorCode::pass();',
        '        }',
        '    }',
        '',
        'private:',
        f'    std::string m_uvmDut = "{defaultDut}";',
        '};',
        '',
        f'[[maybe_unused]] A2C_REGISTRATION_RETAIN int uvmTbConfigRegistered = (testBenchConfigFactory::registerTestBenchConfig(',
        f'    "{uvm["testbenchName"]}",',
        '    [](std::string) -> std::shared_ptr<testBenchConfigBase> { return std::make_shared<uvmTbConfig>(); },',
        '    is_default_testbench_v<uvmTbConfig>), 0);',
        '',
        '} // namespace',
        '#endif // XCELIUM || VCS',
    ]
    return '\n'.join(out) + '\n'
