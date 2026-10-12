//

// GENERATED_CODE_PARAM --block=vltSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlTiming_vltSrc.block;
import vlTiming_vltSrc.base;
import vlTiming_vlt;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlTiming_vlt_ns;
export SC_MODULE(vltSrc), public blockBase, public vltSrcBase
{
private:

public:

    vltSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vltSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void send(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(vltSrc);

// === Block factory registration (vltSrc) ===
void register_vltSrc_variants() {
    instanceFactory::registerBlock("vltSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vltSrc>(blockName, variant, bbMode)); }, "", "vlTiming");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vltSrc_registered = (register_vltSrc_variants(), 0);
} // namespace
// === End block factory registration ===

vltSrc::vltSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vltSrc", name(), bbMode)
        ,vltSrcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(send);
};

// Sends one sample stamped with the time the start-up delay ends, in
// picoseconds. rtl/vltSrc.sv stamps the same time from its own delay.
void vltSrc::send(void)
{
    wait(sc_time(VLT_START_DELAY_PS, SC_PS));
    vltSt sample{};
    sample.stamp = (vltStampT)(sc_time_stamp() / sc_time(1, SC_PS));
    out->push(sample);
}
