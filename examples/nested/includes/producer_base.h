#ifndef PRODUCER_BASE_H
#define PRODUCER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class producerBase : public virtual blockPortBase
{
public:
    virtual ~producerBase() = default;
    // src ports
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_trans_rv_tracker;
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_clock_dest_trans_rv_tracker;
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_clock_rv_tracker;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_trans_rv_size;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_clock_dest_trans_rv_size;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_out< testDataSt > src_trans_dest_clock_rv_size;


    producerBase(std::string name, const char * variant) :
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
class producerInverted : public virtual blockPortBase
{
public:
    // src ports
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_trans_rv_tracker;
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_clock_dest_trans_rv_tracker;
    // testrvTracker->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_clock_rv_tracker;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_trans_rv_size;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_clock_dest_trans_rv_size;
    // testrvSize->uConsumer: Data path test interface
    rdy_vld_in< testDataSt > src_trans_dest_clock_rv_size;


    producerInverted(std::string name) :
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
class producerChannels
{
public:
    // src ports
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


    producerChannels(std::string name, std::string srcName) :
    src_trans_dest_trans_rv_tracker(("src_trans_dest_trans_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_clock_dest_trans_rv_tracker(("src_clock_dest_trans_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_trans_dest_clock_rv_tracker(("src_trans_dest_clock_rv_tracker"+name).c_str(), srcName, "api_list_tracker", 2048, "tracker:cmdid")
    ,src_trans_dest_trans_rv_size(("src_trans_dest_trans_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    ,src_clock_dest_trans_rv_size(("src_clock_dest_trans_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    ,src_trans_dest_clock_rv_size(("src_trans_dest_clock_rv_size"+name).c_str(), srcName, "api_list_size", 2048, "")
    {};
    void bind( producerBase *a, producerInverted *b)
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

#endif //PRODUCER_BASE_H
