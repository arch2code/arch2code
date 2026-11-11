// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=uvmTbConfig
#if defined(XCELIUM) || defined(VCS)
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include "bfmContractCheck.h"
#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
#include "watchDog.h"
#include "uvmMem_uvm_sc_wrapper.h"

namespace {

class uvmTbConfig : public testBenchConfigBase
{
public:
    void addProgramOptions(po::options_description &options) override
    {
        options.add_options()
        ("uvmDut", po::value<std::string>(&m_uvmDut)->default_value("model"), "DUT behind the UVM testbench: model, rtl or both; must match the snapshot")
        ("uvmTop", po::value<std::string>(&m_uvmTop), "UVM testbench top: uvmMem; must match the snapshot");
    }

    bool handleProgramOptions(po::variables_map &vm) override
    {
        if (m_uvmDut != "model" && m_uvmDut != "rtl" && m_uvmDut != "both") {
            std::cerr << "--uvmDut must be model, rtl or both, not " << m_uvmDut << std::endl;
            return false;
        }
        auto top = s_topVariants.find(m_uvmTop);
        if (top == s_topVariants.end()) {
            std::cerr << "--uvmTop must name one of the UVM testbench tops uvmMem, not \"" << m_uvmTop << "\"" << std::endl;
            return false;
        }
        m_variant = top->second;
        return true;
    }

    // No firmware worker threads: the UVM register model programs the block.
    bool createTestBench(void) override
    {
        bfmContractCheck::failOnBreak = true;
        watchDog::stallCheckDisabledByUvm = true;
        uvmMem_uvm_run::rtlDut = m_uvmDut == "rtl" || m_uvmDut == "both";
        uvmMem_uvm_run::modelDut = m_uvmDut == "model" || m_uvmDut == "both";
        instanceFactory::registerInstance("uvmMem", "uvm");
        instanceFactory::createInstance("", "uvmMem", "uvmMem", m_variant.c_str(), "uvmMem");
        return true;
    }

    // A UVM_FATAL ends the run with $finish before uvm_done rises. Under
    // Xcelium sc_start then returns and the run ends here.
    void final(void) override
    {
        if (!uvmMem_uvm_run::completed) {
            errorCode::fail(uvmMem_uvm_run::notFinished);
        } else {
            errorCode::pass();
        }
    }

private:
    std::string m_uvmDut = "model";
    std::string m_uvmTop;
    std::string m_variant;
    inline static const std::map<std::string, std::string> s_topVariants = {{"uvmMem", ""}};
};

[[maybe_unused]] A2C_REGISTRATION_RETAIN int uvmTbConfigRegistered = (testBenchConfigFactory::registerTestBenchConfig(
    "uvmMem_uvm",
    [](std::string) -> std::shared_ptr<testBenchConfigBase> { return std::make_shared<uvmTbConfig>(); },
    is_default_testbench_v<uvmTbConfig>), 0);

} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
