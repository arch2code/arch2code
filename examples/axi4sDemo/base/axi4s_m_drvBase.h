#ifndef AXI4S_M_DRV_BASE_H
#define AXI4S_M_DRV_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=axi4s_m_drv
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "axi4_stream_channel.h"
#include "axi4sDemo_tbIncludes.h"

class axi4s_m_drvBase : public virtual blockPortBase
{
public:
    virtual ~axi4s_m_drvBase() = default;
    // src ports
    // axi4str_t1->u_axi4sDemo: AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_out< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4s_m_drvBase(std::string name, const char * variant) :
        axis4_t1("axis4_t1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t1->setLogging(verbosity);
    };
};
class axi4s_m_drvInverted : public virtual blockPortBase
{
public:
    // src ports
    // axi4str_t1->u_axi4sDemo: AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_in< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4s_m_drvInverted(std::string name) :
        axis4_t1(("axis4_t1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        axis4_t1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        axis4_t1->setLogging(verbosity);
    };
};
class axi4s_m_drvChannels
{
public:
    // src ports
    // AXI4 Stream Interface Type 1 (256 bits data)
    axi4_stream_channel< data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t > axis4_t1;


    axi4s_m_drvChannels(std::string name, std::string srcName) :
    axis4_t1(("axis4_t1"+name).c_str(), srcName, "api_list_size", 256, "")
    {};
    void bind( axi4s_m_drvBase *a, axi4s_m_drvInverted *b)
    {
        a->axis4_t1( axis4_t1 );
        b->axis4_t1( axis4_t1 );
    };
};

// GENERATED_CODE_END
#endif //AXI4S_M_DRV_BASE_H
