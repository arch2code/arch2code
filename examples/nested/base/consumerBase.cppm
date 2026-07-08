//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module consumer.base;
import nested;
using namespace nested_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class consumerBase : public virtual blockPortBase
{
public:
    virtual ~consumerBase() = default;
    // dst ports
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_trans_rv_tracker;
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_in< testDataSt > src_clock_dest_trans_rv_tracker;
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_clock_rv_tracker;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_trans_rv_size;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_in< testDataSt > src_clock_dest_trans_rv_size;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_clock_rv_size;


    consumerBase(std::string name, const char * variant) :
        src_trans_dest_trans_rv_tracker("src_trans_dest_trans_rv_tracker")
        ,src_clock_dest_trans_rv_tracker("src_clock_dest_trans_rv_tracker")
        ,src_trans_dest_clock_rv_tracker("src_trans_dest_clock_rv_tracker")
        ,src_trans_dest_trans_rv_size("src_trans_dest_trans_rv_size")
        ,src_clock_dest_trans_rv_size("src_clock_dest_trans_rv_size")
        ,src_trans_dest_clock_rv_size("src_trans_dest_clock_rv_size")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        src_trans_dest_trans_rv_tracker->setTimed(nsec, mode);
        src_clock_dest_trans_rv_tracker->setTimed(nsec, mode);
        src_trans_dest_clock_rv_tracker->setTimed(nsec, mode);
        src_trans_dest_trans_rv_size->setTimed(nsec, mode);
        src_clock_dest_trans_rv_size->setTimed(nsec, mode);
        src_trans_dest_clock_rv_size->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        src_trans_dest_trans_rv_tracker->setLogging(verbosity);
        src_clock_dest_trans_rv_tracker->setLogging(verbosity);
        src_trans_dest_clock_rv_tracker->setLogging(verbosity);
        src_trans_dest_trans_rv_size->setLogging(verbosity);
        src_clock_dest_trans_rv_size->setLogging(verbosity);
        src_trans_dest_clock_rv_size->setLogging(verbosity);
    };
};
export class consumerInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_trans_rv_tracker;
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_out< testDataSt > src_clock_dest_trans_rv_tracker;
    // uProducer->testrvTracker: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_clock_rv_tracker;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_trans_rv_size;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_out< testDataSt > src_clock_dest_trans_rv_size;
    // uProducer->testrvSize: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_clock_rv_size;


    consumerInverted(std::string name) :
        src_trans_dest_trans_rv_tracker(("src_trans_dest_trans_rv_tracker"+name).c_str())
        ,src_clock_dest_trans_rv_tracker(("src_clock_dest_trans_rv_tracker"+name).c_str())
        ,src_trans_dest_clock_rv_tracker(("src_trans_dest_clock_rv_tracker"+name).c_str())
        ,src_trans_dest_trans_rv_size(("src_trans_dest_trans_rv_size"+name).c_str())
        ,src_clock_dest_trans_rv_size(("src_clock_dest_trans_rv_size"+name).c_str())
        ,src_trans_dest_clock_rv_size(("src_trans_dest_clock_rv_size"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        src_trans_dest_trans_rv_tracker->setTimed(nsec, mode);
        src_clock_dest_trans_rv_tracker->setTimed(nsec, mode);
        src_trans_dest_clock_rv_tracker->setTimed(nsec, mode);
        src_trans_dest_trans_rv_size->setTimed(nsec, mode);
        src_clock_dest_trans_rv_size->setTimed(nsec, mode);
        src_trans_dest_clock_rv_size->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        src_trans_dest_trans_rv_tracker->setLogging(verbosity);
        src_clock_dest_trans_rv_tracker->setLogging(verbosity);
        src_trans_dest_clock_rv_tracker->setLogging(verbosity);
        src_trans_dest_trans_rv_size->setLogging(verbosity);
        src_clock_dest_trans_rv_size->setLogging(verbosity);
        src_trans_dest_clock_rv_size->setLogging(verbosity);
    };
};
export class consumerChannels
{
public:
    // dst ports
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_clock_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_size;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_size;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_clock_rv_size;


    consumerChannels(std::string name, std::string srcName) :
    src_trans_dest_trans_rv_tracker(("src_trans_dest_trans_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_clock_dest_trans_rv_tracker(("src_clock_dest_trans_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_trans_dest_clock_rv_tracker(("src_trans_dest_clock_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_trans_dest_trans_rv_size(("src_trans_dest_trans_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    ,src_clock_dest_trans_rv_size(("src_clock_dest_trans_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    ,src_trans_dest_clock_rv_size(("src_trans_dest_clock_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    {};
    void bind( consumerBase *a, consumerInverted *b)
    {
        a->src_trans_dest_trans_rv_tracker( src_trans_dest_trans_rv_tracker );
        b->src_trans_dest_trans_rv_tracker( src_trans_dest_trans_rv_tracker );
        a->src_clock_dest_trans_rv_tracker( src_clock_dest_trans_rv_tracker );
        b->src_clock_dest_trans_rv_tracker( src_clock_dest_trans_rv_tracker );
        a->src_trans_dest_clock_rv_tracker( src_trans_dest_clock_rv_tracker );
        b->src_trans_dest_clock_rv_tracker( src_trans_dest_clock_rv_tracker );
        a->src_trans_dest_trans_rv_size( src_trans_dest_trans_rv_size );
        b->src_trans_dest_trans_rv_size( src_trans_dest_trans_rv_size );
        a->src_clock_dest_trans_rv_size( src_clock_dest_trans_rv_size );
        b->src_clock_dest_trans_rv_size( src_clock_dest_trans_rv_size );
        a->src_trans_dest_clock_rv_size( src_trans_dest_clock_rv_size );
        b->src_trans_dest_clock_rv_size( src_trans_dest_clock_rv_size );
    };
};

// GENERATED_CODE_END
