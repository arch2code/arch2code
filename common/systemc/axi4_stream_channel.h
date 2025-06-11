// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI4_STREAM_CHANNEL_H
#define AXI4_STREAM_CHANNEL_H

#include "sysc/kernel/sc_dynamic_processes.h"
#include "sysc/communication/sc_communication_ids.h"
#include "sysc/communication/sc_prim_channel.h"
#include "rdy_vld_channel.h"
#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/tracing/sc_trace.h"
#include <typeinfo>
#include <iostream>
#include "portBase.h"
#include "interfaceBase.h"
#include "pingPongBuffer.h"
#include <memory>
#include <vector>
#include <queue>
#include <fmt/format.h>
#include "simpleQueue.h"
#include "axiCommon.h"

template <typename TDATA, typename TID, typename TDEST, typename TUSER>
struct axi4StreamInfoSt
{
    TDATA tdata;
    TDATA tstrb;
    TDATA tkeep;
    TID   tid;
    bool  tlast;
    TDEST tdest;
    TUSER tuser;

    static constexpr unsigned int tdataWidth = TDATA::_bitWidth;
    static constexpr unsigned int tstrbWidth = TDATA::_bitWidth;
    static constexpr unsigned int tkeepWidth = TDATA::_bitWidth;
    static constexpr unsigned int tidWidth = TID::_bitWidth;
    static constexpr unsigned int tlastWidth = 1;
    static constexpr unsigned int tdestWidth = TDEST::_bitWidth;
    static constexpr unsigned int tuserWidth = TUSER::_bitWidth;

    static constexpr unsigned int _bitWidth = tdataWidth + tstrbWidth + tkeepWidth + tidWidth + tlastWidth + tdestWidth + tuserWidth;
    static constexpr unsigned int _byteWidth = (_bitWidth + 7)>>3;
    static constexpr unsigned int _packedSize = (_byteWidth + 7)>>3;

    typedef uint64_t _packedSt[_packedSize];

    axi4StreamInfoSt() {};

    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        return(ss.str());
    }

    static const char * getValueType(void)
    {
        return( TDATA::getValueType() );
    }

    inline uint64_t getStructValue(void) const
    {
        return( tdata.getStructValue() );
    }

};

// sendInfo( T )
//          -------> receiveInfo( &T )


template <class TDATA, class TID, class TDEST, class TUSER>
class axi4_stream_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // receiver interfaces
    virtual void receiveInfo( axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>& ) = 0;

protected:
    // constructor
    axi4_stream_in_if()
        {}

private:
    // disabled
    axi4_stream_in_if( const axi4_stream_in_if<TDATA, TID, TDEST, TUSER>& );
    axi4_stream_in_if<TDATA, TID, TDEST, TUSER>& operator = ( const axi4_stream_in_if<TDATA, TID, TDEST, TUSER>& );
};


template <class TDATA, class TID, class TDEST, class TUSER>
class axi4_stream_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // sender interfaces
    virtual void sendInfo( const axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>&, std::optional<std::string> str=std::nullopt ) = 0;

protected:
    // constructor
    axi4_stream_out_if()
        {}

private:
    // disabled
    axi4_stream_out_if( const axi4_stream_out_if<TDATA, TID, TDEST, TUSER>& );
    axi4_stream_out_if<TDATA, TID, TDEST, TUSER>& operator = ( const axi4_stream_out_if<TDATA, TID, TDEST, TUSER>& );
};

class axi4_stream_transaction_counter {
public:
    inline static uint64_t transactionNo{0};
};

template <class TDATA, class TID, class TDEST, class TUSER>
class axi4_stream_channel
: public axi4_stream_in_if<TDATA, TID, TDEST, TUSER>,
  public axi4_stream_out_if<TDATA, TID, TDEST, TUSER>,
  public sc_prim_channel,
  public axi4_stream_transaction_counter
{
public:
    // constructor const char * module, std::string block
    explicit axi4_stream_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        m_tx_channel((std::string(name_) + "tx").c_str(), block_),
        m_tx_out((std::string(name_) + "txOut").c_str()),
        m_tx_in((std::string(name_) + "txIn").c_str()),
        m_reader(nullptr),
        m_writer(nullptr),
        m_logQueue(std::make_shared<stringPingPong>())
        {
            m_tx_in( m_tx_channel );
            m_tx_out( m_tx_channel );
            m_tx_channel.setLogQueue(m_logQueue);
        }

    explicit axi4_stream_channel( const char* name_, std::string block_, std::string multiCycleType_, int pingpong_size_, std::string trackerName_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
        : sc_prim_channel( name_ ),
        m_tx_channel((std::string(name_) + "tx").c_str(), block_),
        m_tx_out((std::string(name_) + "txOut").c_str()),
        m_tx_in((std::string(name_) + "txIn").c_str()),
        m_reader(nullptr),
        m_writer(nullptr),
        m_logQueue(std::make_shared<stringPingPong>())
        {   
            m_tx_in( m_tx_channel );
            m_tx_out( m_tx_channel );
            m_tx_channel.setLogQueue(m_logQueue);
        }
    
    // destructor
    virtual ~axi4_stream_channel() { }

    // out interface 
    virtual void sendInfo(const axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>&, std::optional<std::string> str ) override;

    // in interface
    virtual void receiveInfo( axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>& ) override;

    void setMultiDriver(std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        Q_ASSERT(false, fmt::format("multiple drivers on {} axiWr interface is invalid", name_ ));
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (m_tx_in->getTracker());}
    virtual void setTeeBusy(bool busy) override { m_tx_in->setTeeBusy(busy); }
    virtual void setTandem(void) override { m_tx_channel.setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { m_tx_channel.setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { m_tx_channel.setTimed(nsec, mode); }

protected:
    rdy_vld_channel<axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>> m_tx_channel;
public: // make these public for the tees/verif
    rdy_vld_out <axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>> m_tx_out;
    rdy_vld_in <axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>> m_tx_in;

protected:
    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

private:
    // disabled
    axi4_stream_channel( const axi4_stream_channel<TDATA, TID, TDEST, TUSER>& );
    axi4_stream_channel& operator = ( const axi4_stream_channel<TDATA, TID, TDEST, TUSER>& );
    std::shared_ptr<stringPingPong> m_logQueue;
};

// blocking transactional read
template <class TDATA, class TID, class TDEST, class TUSER>
inline void axi4_stream_channel<TDATA, TID, TDEST, TUSER>::receiveInfo( axi4StreamInfoSt<TDATA, TID, TDEST, TUSER> &info_ )
{
    m_tx_in->read(info_);
}

// blocking transactional read
template <class TDATA, class TID, class TDEST, class TUSER>
inline void axi4_stream_channel<TDATA, TID, TDEST, TUSER>::sendInfo(const axi4StreamInfoSt<TDATA, TID, TDEST, TUSER> &info_, std::optional<std::string> str )
{
    m_tx_out->write(info_);
}

template <class TDATA, class TID, class TDEST, class TUSER>
using axi4_stream_out = sc_port<axi4_stream_out_if<TDATA, TID, TDEST, TUSER> >;
template <class TDATA, class TID, class TDEST, class TUSER>
using axi4_stream_in = sc_port<axi4_stream_in_if<TDATA, TID, TDEST, TUSER> >;

#endif // AXI4_STREAM_CHANNEL_H
