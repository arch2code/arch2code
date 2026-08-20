//

// GENERATED_CODE_PARAM --block=xpDpSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpTop_xpDpSrc.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpSrcBase : public virtual blockPortBase
{
public:
    virtual ~xpDpSrcBase() = default;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // src ports
    // dpIf->uMid: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out;
    // dpIf->uLeafX: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out2;
    // dpIf->uMid2: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out4;
    // dpIf->uMid3: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out3;


    xpDpSrcBase(std::string name, const char * variant) :
        out("out")
        ,out2("out2")
        ,out4("out4")
        ,out3("out3")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        out4->setTimed(nsec, mode);
        out3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        out2->setLogging(verbosity);
        out4->setLogging(verbosity);
        out3->setLogging(verbosity);
    };
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // dpIf->uMid: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out;
    // dpIf->uLeafX: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out2;
    // dpIf->uMid2: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out4;
    // dpIf->uMid3: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out3;


    xpDpSrcInverted(std::string name) :
        out(("out"+name).c_str())
        ,out2(("out2"+name).c_str())
        ,out4(("out4"+name).c_str())
        ,out3(("out3"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        out2->setTimed(nsec, mode);
        out4->setTimed(nsec, mode);
        out3->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        out2->setLogging(verbosity);
        out4->setLogging(verbosity);
        out3->setLogging(verbosity);
    };
};
export template<typename Config>
class xpDpSrcChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out2;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out4;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out3;


    xpDpSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,out2(("out2"+name).c_str(), srcName)
    ,out4(("out4"+name).c_str(), srcName)
    ,out3(("out3"+name).c_str(), srcName)
    {};
    void bind( xpDpSrcBase<Config> *a, xpDpSrcInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->out2( out2 );
        b->out2( out2 );
        a->out4( out4 );
        b->out4( out4 );
        a->out3( out3 );
        b->out3( out3 );
    };
};

// GENERATED_CODE_END
