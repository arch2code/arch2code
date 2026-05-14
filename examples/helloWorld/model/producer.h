#ifndef PRODUCER_H
#define PRODUCER_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "producer_base.h"
#include "helloWorldTopIncludes.h"

SC_MODULE(producer), public blockBase, public producerBase
{
private:

public:

    producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~producer() override = default;

    // GENERATED_CODE_END

    // block implementation members
    void producerOutRdyVld(void);
    void producerOutPushAck(void);
    void producerOutReqAck(void);
    void producerOutPopAck(void);
};

#endif //PRODUCER_H

