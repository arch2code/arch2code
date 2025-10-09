#ifndef AXI4SDEMO_BASE_H
#define AXI4SDEMO_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "axi4_stream_channel.h"
#include "axi4sDemo_tbIncludes.h"

class axi4sDemoBase : public virtual blockPortBase
{
public:
    virtual ~axi4sDemoBase() = default;
    // src ports
    // axi4str_t2->u_axi4s_s_drv: AXI4 Stream Interface Type 2 (64 bits data)
    axi4_stream_out< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;

    // dst ports
    // u_axi4s_m_drv->axi4str_t1: AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_in< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4sDemoBase(std::string name, const char * variant) :
        axis4_t2("axis4_t2")
        ,axis4_t1("axis4_t1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t2->setTimed(nsec, mode);
        axis4_t1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t2->setLogging(verbosity);
        axis4_t1->setLogging(verbosity);
    };
};
class axi4sDemoInverted : public virtual blockPortBase
{
public:
    // src ports
    // axi4str_t2->u_axi4s_s_drv: AXI4 Stream Interface Type 2 (64 bits data)
    axi4_stream_in< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;

    // dst ports
    // u_axi4s_m_drv->axi4str_t1: AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_out< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4sDemoInverted(std::string name) :
        axis4_t2(("axis4_t2"+name).c_str())
        ,axis4_t1(("axis4_t1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t2->setTimed(nsec, mode);
        axis4_t1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t2->setLogging(verbosity);
        axis4_t1->setLogging(verbosity);
    };
};
class axi4sDemoChannels
{
public:
    // src ports
    // AXI4 Stream Interface Type 2 (64 bits data)
    axi4_stream_channel< data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t > axis4_t2;

    // dst ports
    // AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_channel< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4sDemoChannels(std::string name, std::string srcName) :
    axis4_t2(("axis4_t2"+name).c_str(), srcName, "api_list_size", 64, "")
    ,axis4_t1(("axis4_t1"+name).c_str(), srcName, "api_list_size", 256, "")
    {};
    void bind( axi4sDemoBase *a, axi4sDemoInverted *b)
    {
        a->axis4_t2( axis4_t2 );
        b->axis4_t2( axis4_t2 );
        a->axis4_t1( axis4_t1 );
        b->axis4_t1( axis4_t1 );
    };
};

// GENERATED_CODE_END
#endif //AXI4SDEMO_BASE_H
