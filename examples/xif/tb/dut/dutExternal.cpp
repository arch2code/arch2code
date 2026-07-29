#include "dutExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=xif_tb --excludeInst=uDut

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import src.base;
import sink.base;

dutExternal::dutExternal(sc_module_name modulename) :
    dutInverted<xifDefaultConfig>("Chnl"),
    log_(name())

   ,uSrc(std::dynamic_pointer_cast<srcBase<xifDefaultConfig>>(instanceFactory::createInstance(name(), "uSrc", "src", "srcV0", "xif")))
   ,uSink(std::dynamic_pointer_cast<sinkBase<xifDefaultConfig>>(instanceFactory::createInstance(name(), "uSink", "sink", "sinkV0", "xif")))
   ,thunker_out_uSrc("thunker_out_uSrc", streamIn, uSrc->out, name())
   ,thunker_streamOut_uSink("thunker_streamOut_uSink", streamOut, uSink->in, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
