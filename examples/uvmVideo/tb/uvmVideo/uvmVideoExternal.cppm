//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo_tb --excludeInst=u_uvmVideo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module uvmVideo.external;
import a2c.endOfTest;
import uvmVideo.base;
import uvmVideo_uvmVideoSrc.base;
import uvmVideo_uvmVideoSink.base;
import uvmVideo;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace uvmVideo_ns;

export class uvmVideoExternal: public sc_module, public uvmVideoInverted {

    logBlock log_;

public:

    std::shared_ptr<uvmVideoSrcBase> uSrc;
    std::shared_ptr<uvmVideoSinkBase> uSink;

    SC_HAS_PROCESS (uvmVideoExternal);

    uvmVideoExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

uvmVideoExternal::uvmVideoExternal(sc_module_name modulename) :
    uvmVideoInverted("Chnl"),
    log_(name())

   ,uSrc(std::dynamic_pointer_cast<uvmVideoSrcBase>(instanceFactory::createInstance(name(), "uSrc", "uvmVideoSrc", "", "uvmVideo")))
   ,uSink(std::dynamic_pointer_cast<uvmVideoSinkBase>(instanceFactory::createInstance(name(), "uSink", "uvmVideoSink", "", "uvmVideo")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uSrc->out(vin);
    uSink->in(vout);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};
