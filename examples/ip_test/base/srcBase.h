#ifndef SRC_BASE_H
#define SRC_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
import src;
using namespace src_ns;
import ipLeaf;
using namespace ipLeaf_ns;

template<typename Config>
class srcBase : public virtual blockPortBase
{
public:
    virtual ~srcBase() = default;
    const uint64_t OUT0_DATA_WIDTH;
    const uint64_t OUT1_DATA_WIDTH;
    // src ports
    // srcOut0If->uIp0: src out0 push/ack stream
    push_ack_out< srcOut0St<Config> > out0;
    // srcOut1If->uIp1: src out1 push/ack stream
    push_ack_out< srcOut1St<Config> > out1;


    srcBase(std::string name, const char * variant) :
        OUT0_DATA_WIDTH(Config::OUT0_DATA_WIDTH)
        ,OUT1_DATA_WIDTH(Config::OUT1_DATA_WIDTH)
        ,out0("out0")
        ,out1("out1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
    };
};
template<typename Config>
class srcInverted : public virtual blockPortBase
{
public:
    // src ports
    // srcOut0If->uIp0: src out0 push/ack stream
    push_ack_in< srcOut0St<Config> > out0;
    // srcOut1If->uIp1: src out1 push/ack stream
    push_ack_in< srcOut1St<Config> > out1;


    srcInverted(std::string name) :
        out0(("out0"+name).c_str())
        ,out1(("out1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
    };
};
template<typename Config>
class srcChannels
{
public:
    // src ports
    // src out0 push/ack stream
    push_ack_channel< srcOut0St<Config> > out0;
    // src out1 push/ack stream
    push_ack_channel< srcOut1St<Config> > out1;


    srcChannels(std::string name, std::string srcName) :
    out0(("out0"+name).c_str(), srcName)
    ,out1(("out1"+name).c_str(), srcName)
    {};
    void bind( srcBase<Config> *a, srcInverted<Config> *b)
    {
        a->out0( out0 );
        b->out0( out0 );
        a->out1( out1 );
        b->out1( out1 );
    };
};

// GENERATED_CODE_END
#endif //SRC_BASE_H
