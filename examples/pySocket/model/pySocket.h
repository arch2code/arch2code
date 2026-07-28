#ifndef PYSOCKET_H
#define PYSOCKET_H

//

#include "systemc.h"
#include <list>

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import pySocket.base;
#include "req_ack_channel.h"
import pySocket_tb;
using namespace pySocket_tb_ns;

SC_MODULE(pySocket), public blockBase, public pySocketBase
{
private:

public:

    pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket() override = default;

    // GENERATED_CODE_END
    std::list<p2s_message_st> p2s_message_list;
};

#endif //PYSOCKET_H
