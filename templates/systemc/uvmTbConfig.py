# The UVM testbench config of a hasUvm block. It creates the SystemC wrapper
# through the instanceFactory under the block's own name, at the variant of
# the top --uvmTop names and with the DUT --uvmDut picks. The wrapper fails
# the run for UVM errors. When UVM never finishes, as when a UVM_FATAL calls
# $finish, final() fails the run under Xcelium, where sc_start returns. Under
# VCS the $finish skips final(), and main.cpp's exit_handler fails the run.
# Both options are elaboration arguments of the snapshot, so a run repeats
# them.
# Only the Xcelium and VCS builds compile it, because it selects the
# <block>_uvm factory entry that only the registrar registers, and the
# registrar is built only there.
def render(args, prj, data):
    uvm = data['uvm']
    blockName = data['blockName']
    run = uvm['runClass']
    project = prj.config.getConfig('PROJECTNAME')
    topVariants = [f'{{"{top["stem"]}", "{variant}"}}' for variant, top in uvm['tops'].items()]
    topNames = ', '.join(top['stem'] for top in uvm['tops'].values())
    duts = uvm['duts']
    defaultDut = duts[0]
    choices = ' or '.join(duts)
    why = '' if 'model' in duts else f', because {blockName} has no model'
    mismatch = ' && '.join(f'm_uvmDut != "{dut}"' for dut in duts)
    dutCheck = [
        f'        if ({mismatch}) {{',
        f'            std::cerr << "--uvmDut must be {choices}{why}, not " << m_uvmDut << std::endl;',
        '            return false;',
        '        }',
    ]
    dutHelp = f'DUT behind the UVM testbench: {choices}{why}' + ('' if why else '; must match the snapshot')
    out = [
        '#if defined(XCELIUM) || defined(VCS)',
        '#include <iostream>',
        '#include <map>',
        '#include <memory>',
        '#include <string>',
        '#include "bfmContractCheck.h"',
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
        f'        ("uvmDut", po::value<std::string>(&m_uvmDut)->default_value("{defaultDut}"), "{dutHelp}")',
        f'        ("uvmTop", po::value<std::string>(&m_uvmTop), "UVM testbench top: {topNames}; must match the snapshot");',
        '    }',
        '',
        '    bool handleProgramOptions(po::variables_map &vm) override',
        '    {',
        *dutCheck,
        '        auto top = s_topVariants.find(m_uvmTop);',
        '        if (top == s_topVariants.end()) {',
        f'            std::cerr << "--uvmTop must name one of the UVM testbench tops {topNames}, not \\"" << m_uvmTop << "\\"" << std::endl;',
        '            return false;',
        '        }',
        '        m_variant = top->second;',
        '        return true;',
        '    }',
        '',
        '    // No firmware worker threads: the UVM register model programs the block.',
        '    bool createTestBench(void) override',
        '    {',
        '        bfmContractCheck::failOnBreak = true;',
        f'        {run}::rtlDut = m_uvmDut == "rtl";',
        f'        instanceFactory::registerInstance("{blockName}", "uvm");',
        f'        instanceFactory::createInstance("", "{blockName}", "{blockName}", m_variant.c_str(), "{project}");',
        '        return true;',
        '    }',
        '',
        '    // A UVM_FATAL ends the run with $finish before uvm_done rises. Under',
        '    // Xcelium sc_start then returns and the run ends here.',
        '    void final(void) override',
        '    {',
        f'        if (!{run}::completed) {{',
        f'            errorCode::fail({run}::notFinished);',
        '        } else {',
        '            errorCode::pass();',
        '        }',
        '    }',
        '',
        'private:',
        f'    std::string m_uvmDut = "{defaultDut}";',
        '    std::string m_uvmTop;',
        '    std::string m_variant;',
        f'    inline static const std::map<std::string, std::string> s_topVariants = {{{", ".join(topVariants)}}};',
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
