//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --variant=variant0 --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module ip.external;
import a2c.endOfTest;
import ip.base;
import ip.ip.config;
import ip;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace ip_ns;

export class ipExternal: public sc_module, public ipInverted<ip_ipVariant0Config> {

    logBlock log_;

public:

    SC_HAS_PROCESS (ipExternal);

    ipExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // Directed stimulus: push one transaction whose payload satisfies the
    // asserts in ip::dataHandler (marker == 1, high data word == 0x2A for
    // IP_DATA_WIDTH > 64), then vote end-of-test. Reaching the line after
    // push() is the functional assertion that the DUT acked.
    void stimulusThread(void);

private:
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

ipExternal::ipExternal(sc_module_name modulename) :
    ipInverted<ip_ipVariant0Config>("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
    SC_THREAD(stimulusThread);
};

void ipExternal::stimulusThread(void)
{
    wait(SC_ZERO_TIME);

    ipDataT<ip_ipVariant0Config> payload{};
    payload.word[0] = 0xDEADBEEFCAFEBABEULL;
    payload.word[1] = 0x2A;
    ipDataSt<ip_ipVariant0Config> data(payload, static_cast<enableT>(1));

    log_.logPrint(std::format("{} stimulusThread pushing data 0x{:x}{:016x} marker {}",
                              name(), data.data.word[1], data.data.word[0],
                              static_cast<uint64_t>(data.marker)),
                  LOG_IMPORTANT);
    ipDataIf->push(data);
    log_.logPrint(std::format("{} stimulusThread received ack, voting end-of-test", name()),
                  LOG_IMPORTANT);

    eot_.setEndOfTest(true);
}

