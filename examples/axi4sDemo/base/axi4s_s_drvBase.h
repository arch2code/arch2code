#ifndef AXI4S_S_DRV_BASE_H
#define AXI4S_S_DRV_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axi4s_s_drv
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "axi4_stream_channel.h"
#include "axi4sDemo_tbIncludes.h"

class axi4s_s_drvBase : public virtual blockPortBase
{
public:
    virtual ~axi4s_s_drvBase() = default;
    // src ports

    // dst ports
    // u_axi4sDemo->axi4str_t2: AXI4 Stream Interface Type 2 (64 bits data)
    axi4_stream_in< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;


    axi4s_s_drvBase(std::string name, const char * variant) :
        axis4_t2("axis4_t2")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t2->setLogging(verbosity);
    };
};
class axi4s_s_drvInverted : public virtual blockPortBase
{
public:
    // src ports

    // dst ports
    // u_axi4sDemo->axi4str_t2: AXI4 Stream Interface Type 2 (64 bits data)
    axi4_stream_out< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;


    axi4s_s_drvInverted(std::string name) :
        axis4_t2(("axis4_t2"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t2->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t2->setLogging(verbosity);
    };
};
class axi4s_s_drvChannels
{
public:
    // src ports

    // dst ports
    //   axi4str_t2
    axi4_stream_channel< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;


    axi4s_s_drvChannels(std::string name, std::string srcName) :
    axis4_t2(("axis4_t2"+name).c_str(), srcName, "api_list_size", 64, "")
    {};
    void bind( axi4s_s_drvBase *a, axi4s_s_drvInverted *b)
    {
        a->axis4_t2( axis4_t2 );
        b->axis4_t2( axis4_t2 );
    };
};

// GENERATED_CODE_END
#endif //AXI4S_S_DRV_BASE_H
