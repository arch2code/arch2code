//

// GENERATED_CODE_PARAM --block=xpSktLeaf
// GENERATED_CODE_BEGIN --template=socket --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_port_socket.h"
#include "xpSktLeafSocketCatalog.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "asyncEvent.h"
// GENERATED_CODE_BEGIN --template=socket --section=moduleExport
export module xpSktIp_xpSktLeaf.socket;
import xpSktIp_xpSktLeaf.base;
import xpSktIp.xpSktLeaf.config;
import xpSktIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=socket --section=socket
export template<typename Config>
SC_MODULE(xpSktLeafSocket), public blockBase, public xpSktLeafBase<Config>
{
public:
    SC_HAS_PROCESS(xpSktLeafSocket);

    xpSktLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSktLeafSocket() override = default;

private:
    void outSocket(void);

// GENERATED_CODE_END
    // socket shell members
private:
    // Python traffic arrives through thread-safe events, which do not keep the
    // kernel from running out of events, so the shell advances time itself.
    void simHeartbeat(void);

};

// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
template<typename Config>
void xpSktLeafSocket<Config>::outSocket(void) {
    Q_ASSERT(socketFactory::getPort(xpSktLeafSocketCatalog::name_out(this->name())) != 0,
             "socket " + xpSktLeafSocketCatalog::name_out(this->name()) + " is not registered; the testbench must registerInstance this shell's instance path");
    port_socket(this->out, xpSktLeafSocketCatalog::name_out(this->name()));
}

template<typename Config>
xpSktLeafSocket<Config>::xpSktLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSktLeaf", name(), bbMode)
        ,xpSktLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(outSocket);

// GENERATED_CODE_END
    // ThreadSafeEvent is a primitive channel, so it must exist before
    // simulation starts; port_socket() reuses it by name.
    (void)ThreadSafeEventFactory::newEvent((xpSktLeafSocketCatalog::name_out(this->name()) + "_push").c_str());
    SC_THREAD(simHeartbeat);
}
// user method definitions here

template<typename Config>
void xpSktLeafSocket<Config>::simHeartbeat(void)
{
    while (true) {
        wait(sc_time(1, SC_US));
    }
}
