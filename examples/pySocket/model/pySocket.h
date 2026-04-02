#ifndef PYSOCKET_H
#define PYSOCKET_H

//

#include "systemc.h"
#include <list>

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "pySocketBase.h"
#include "pySocketIncludes.h"

SC_MODULE(pySocket), public blockBase, public pySocketBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("pySocket_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<pySocket>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void python2SystemCTest(void);
    void systemC2PythonTest(void);
    void python2SystemCEventThread(void);
    sc_event p2s_dataReadyEvent;
    sc_event p2s_startEvent;
    std::list<p2s_message_st> p2s_message_list;
};

#endif //PYSOCKET_H
