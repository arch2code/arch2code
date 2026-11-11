//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem_tb --excludeInst=u_uvmMem --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module uvmMem.external;
import a2c.endOfTest;
import uvmMem.base;
import uvmMem_uvmMemSrc.base;
import uvmMem_uvmMemSink.base;
import uvmMem_uvmMemStore.base;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace uvmMem_ns;

export class uvmMemExternal: public sc_module, public uvmMemInverted {

    logBlock log_;

public:

    std::shared_ptr<uvmMemSrcBase> uSrc;
    std::shared_ptr<uvmMemSinkBase> uSink;
    std::shared_ptr<uvmMemStoreBase> uStore;

    SC_HAS_PROCESS (uvmMemExternal);

    uvmMemExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

uvmMemExternal::uvmMemExternal(sc_module_name modulename) :
    uvmMemInverted("Chnl"),
    log_(name())

   ,uSrc(std::dynamic_pointer_cast<uvmMemSrcBase>(instanceFactory::createInstance(name(), "uSrc", "uvmMemSrc", "", "uvmMem")))
   ,uSink(std::dynamic_pointer_cast<uvmMemSinkBase>(instanceFactory::createInstance(name(), "uSink", "uvmMemSink", "", "uvmMem")))
   ,uStore(std::dynamic_pointer_cast<uvmMemStoreBase>(instanceFactory::createInstance(name(), "uStore", "uvmMemStore", "", "uvmMem")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uSrc->cmd(cmd);
    uSink->in(out);
    uStore->wr(wr);
    uStore->rd(rd);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};
