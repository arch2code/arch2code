//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module ip_test_src.base;
import ip_test_src;
import ip_test_ipLeaf;
using namespace ip_test_src_ns;
using namespace ip_test_ipLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class srcBase : public virtual blockPortBase
{
public:
    virtual ~srcBase() = default;
    static constexpr auto OUT0_DATA_WIDTH = Config::OUT0_DATA_WIDTH;
    static constexpr auto OUT1_DATA_WIDTH = Config::OUT1_DATA_WIDTH;
    // src ports
    // srcOut0If->uIp0: src out0 push/ack stream
    push_ack_out< srcOut0St<Config> > out0;
    // srcOut1If->uIp1: src out1 push/ack stream
    push_ack_out< srcOut1St<Config> > out1;
    // srcOut0If->uBridge: src out0 push/ack stream
    push_ack_out< srcOut0St<Config> > out2;
    // srcOut1If->uBridge: src out1 push/ack stream
    push_ack_out< srcOut1St<Config> > out3;


    srcBase(std::string name, const char * variant) :
        out0("out0")
        ,out1("out1")
        ,out2("out2")
        ,out3("out3")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        out3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
        out2->setLogging(verbosity);
        out3->setLogging(verbosity);
    };
    using srcOut0DataT = srcOut0DataT<Config>;
    using srcOut1DataT = srcOut1DataT<Config>;
    using srcOut0St = srcOut0St<Config>;
    using srcOut1St = srcOut1St<Config>;
};
export template<typename Config>
class srcInverted : public virtual blockPortBase
{
public:
    // src ports
    // srcOut0If->uIp0: src out0 push/ack stream
    push_ack_in< srcOut0St<Config> > out0;
    // srcOut1If->uIp1: src out1 push/ack stream
    push_ack_in< srcOut1St<Config> > out1;
    // srcOut0If->uBridge: src out0 push/ack stream
    push_ack_in< srcOut0St<Config> > out2;
    // srcOut1If->uBridge: src out1 push/ack stream
    push_ack_in< srcOut1St<Config> > out3;


    srcInverted(std::string name) :
        out0(("out0"+name).c_str())
        ,out1(("out1"+name).c_str())
        ,out2(("out2"+name).c_str())
        ,out3(("out3"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out0->setTimed(nsec, mode);
        out1->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        out3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out0->setLogging(verbosity);
        out1->setLogging(verbosity);
        out2->setLogging(verbosity);
        out3->setLogging(verbosity);
    };
};
export template<typename Config>
class srcChannels
{
public:
    // src ports
    // src out0 push/ack stream
    push_ack_channel< srcOut0St<Config> > out0;
    // src out1 push/ack stream
    push_ack_channel< srcOut1St<Config> > out1;
    // src out0 push/ack stream
    push_ack_channel< srcOut0St<Config> > out2;
    // src out1 push/ack stream
    push_ack_channel< srcOut1St<Config> > out3;


    srcChannels(std::string name, std::string srcName) :
    out0(("out0"+name).c_str(), srcName)
    ,out1(("out1"+name).c_str(), srcName)
    ,out2(("out2"+name).c_str(), srcName)
    ,out3(("out3"+name).c_str(), srcName)
    {};
    void bind( srcBase<Config> *a, srcInverted<Config> *b)
    {
        a->out0( out0 );
        b->out0( out0 );
        a->out1( out1 );
        b->out1( out1 );
        a->out2( out2 );
        b->out2( out2 );
        a->out3( out3 );
        b->out3( out3 );
    };
};

// GENERATED_CODE_END
