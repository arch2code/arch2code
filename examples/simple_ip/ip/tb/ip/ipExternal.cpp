#include "ipExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=ip --variant=variant0

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

ipExternal::ipExternal(sc_module_name modulename) :
    ipInverted<ipVariant0Config>("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(stimulusThread);
}

void ipExternal::stimulusThread(void)
{
    wait(SC_ZERO_TIME);

    ipDataT<ipVariant0Config> payload{};
    payload.word[0] = 0xDEADBEEFCAFEBABEULL;
    payload.word[1] = 0x2A;
    ipDataSt<ipVariant0Config> data(payload, static_cast<enableT>(1));

    log_.logPrint(std::format("{} stimulusThread pushing data 0x{:x}{:016x} marker {}",
                              name(), data.data.word[1], data.data.word[0],
                              static_cast<uint64_t>(data.marker)),
                  LOG_IMPORTANT);
    ipDataIf->push(data);
    log_.logPrint(std::format("{} stimulusThread received ack, voting end-of-test", name()),
                  LOG_IMPORTANT);

    eot_.setEndOfTest(true);
}
