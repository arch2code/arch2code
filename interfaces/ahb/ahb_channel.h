// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AHB_CHANNEL_H
#define AHB_CHANNEL_H

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
#include "bitTwiddling.h"
#include <memory>
#include <queue>
#include <format>
#include "ahbCommon.h"

// sendAddr( A )
//          -------> receiveAddr( &A )
// sendData( D )                          writes only
//          -------> receiveData( &D )
//                   sendResp( R )
// receiveResp( &R ) <-------
//
// Each transfer has an address phase (sendAddr) and a data phase (sendData for a
// write, then receiveResp). The phases run on separate sub-channels, so a manager
// with one thread per phase can issue the address of transfer N+1 while transfer
// N is in its data phase. Data phases complete in address order.

template <typename A>
struct ahbAddrSt
{
    A           haddr;     // Transfer address
    _ahbTransT  htrans;    // Transfer type, NONSEQ or SEQ for a transfer the subordinate acts on
    bool        hwrite;    // One write, zero read
    _ahbSizeT   hsize;     // Bytes in transfer, encoded as log2
    _ahbBurstT  hburst;    // Burst type and length
    _ahbProtT   hprot;     // Protection control
    bool        hmastlock; // Locked sequence

    static constexpr unsigned int addrWidth = A::_bitWidth; // number of bits in haddr
    static constexpr unsigned int transWidth = AHB_TRANS_WIDTH; // number of bits in htrans
    static constexpr unsigned int writeWidth = 1; // number of bits in hwrite
    static constexpr unsigned int sizeWidth = AHB_SIZE_WIDTH; // number of bits in hsize
    static constexpr unsigned int burstWidth = AHB_BURST_WIDTH; // number of bits in hburst
    static constexpr unsigned int protWidth = AHB_PROT_WIDTH; // number of bits in hprot
    static constexpr unsigned int mastlockWidth = 1; // number of bits in hmastlock

    static constexpr unsigned int _bitWidth = addrWidth + transWidth + writeWidth + sizeWidth + burstWidth + protWidth + mastlockWidth;
    static constexpr unsigned int _byteWidth = (_bitWidth + 7)>>3;
    static constexpr unsigned int _packedSize = (_byteWidth + 7)>>3;

    typedef uint64_t _packedSt[_packedSize];

    ahbAddrSt() : htrans(AHBTRANS_NONSEQ), hwrite(false), hsize(0), hburst(AHBBURST_SINGLE), hprot(0), hmastlock(false) {}

    inline bool operator == (const ahbAddrSt< A > & rhs) const {
        return (
            rhs.haddr == haddr &&
            rhs.htrans == htrans &&
            rhs.hwrite == hwrite &&
            rhs.hsize == hsize &&
            rhs.hburst == hburst &&
            rhs.hprot == hprot &&
            rhs.hmastlock == hmastlock
        );
    }
    inline friend void sc_trace(sc_trace_file *tf, const ahbAddrSt< A > & v, const std::string & NAME ) {
        sc_trace(tf,v.haddr, NAME + ".haddr");
        sc_trace(tf,v.htrans, NAME + ".htrans");
        sc_trace(tf,v.hwrite, NAME + ".hwrite");
        sc_trace(tf,v.hsize, NAME + ".hsize");
        sc_trace(tf,v.hburst, NAME + ".hburst");
        sc_trace(tf,v.hprot, NAME + ".hprot");
        sc_trace(tf,v.hmastlock, NAME + ".hmastlock");
    }
    inline friend ostream& operator << ( ostream& os, ahbAddrSt< A > const & v ) {
        os << "("
           << v.haddr.prt() << ", "
           << _ahbTransT_prt(v.htrans) << ", "
           << (int)v.hwrite << ", "
           << (int)v.hsize << ", "
           << _ahbBurstT_prt(v.hburst) << ", "
           << (int)v.hprot << ", "
           << (int)v.hmastlock << ");";
        return os;
    }
    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        ss << "haddr:" << haddr.prt()
           << " htrans:" << _ahbTransT_prt(htrans)
           << " hwrite:0x" << std::hex << std::setw(1) << (int)hwrite
           << " hsize:0x" << std::hex << std::setw(1) << (int)hsize
           << " hburst:" << _ahbBurstT_prt(hburst)
           << " hprot:0x" << std::hex << std::setw(1) << (int)hprot
           << " hmastlock:0x" << std::hex << std::setw(1) << (int)hmastlock;
        return(ss.str());
    }
    static const char * getValueType(void)
    {
        return( A::getValueType() );
    }
    inline uint64_t getStructValue(void) const
    {
        return( haddr.getStructValue() );
    }
    inline void pack(_packedSt &_ret) const
    {
        uint16_t _pos{0};
        memset(&_ret, 0, ahbAddrSt::_byteWidth);
        pack_payload_bits((uint64_t *)&_ret, _pos, haddr, addrWidth);
        _pos += addrWidth;
        pack_bits((uint64_t *)&_ret, _pos, htrans, transWidth);
        _pos += transWidth;
        pack_bits((uint64_t *)&_ret, _pos, hwrite, writeWidth);
        _pos += writeWidth;
        pack_bits((uint64_t *)&_ret, _pos, hsize, sizeWidth);
        _pos += sizeWidth;
        pack_bits((uint64_t *)&_ret, _pos, hburst, burstWidth);
        _pos += burstWidth;
        pack_bits((uint64_t *)&_ret, _pos, hprot, protWidth);
        _pos += protWidth;
        pack_bits((uint64_t *)&_ret, _pos, hmastlock, mastlockWidth);
        _pos += mastlockWidth;
    }
    inline void unpack(_packedSt &_src)
    {
        uint16_t _pos{0};
        unpack_payload_bits(haddr, _src, _pos, addrWidth);
        _pos += addrWidth;
        unpack_scalar_bits(htrans, _src, _pos, transWidth);
        _pos += transWidth;
        unpack_scalar_bits(hwrite, _src, _pos, writeWidth);
        _pos += writeWidth;
        unpack_scalar_bits(hsize, _src, _pos, sizeWidth);
        _pos += sizeWidth;
        unpack_scalar_bits(hburst, _src, _pos, burstWidth);
        _pos += burstWidth;
        unpack_scalar_bits(hprot, _src, _pos, protWidth);
        _pos += protWidth;
        unpack_scalar_bits(hmastlock, _src, _pos, mastlockWidth);
        _pos += mastlockWidth;
    }

};

template <typename D>
struct ahbRespSt
{
    D       hrdata; // Read data, unused on a write
    bool    hresp;  // One ERROR, zero OKAY

    static constexpr unsigned int dataWidth = D::_bitWidth; // number of bits in hrdata
    static constexpr unsigned int respWidth = 1; // number of bits in hresp

    static constexpr unsigned int _bitWidth = dataWidth + respWidth;
    static constexpr unsigned int _byteWidth = (_bitWidth + 7)>>3;
    static constexpr unsigned int _packedSize = (_byteWidth + 7)>>3;

    typedef uint64_t _packedSt[_packedSize];

    // A generated payload's constructor leaves its fields unset, and a write
    // response carries no read data, so hrdata starts at zero.
    ahbRespSt() : hresp(false)
    {
        typename D::_packedSt zero{};
        hrdata.unpack(zero);
    }

    inline bool operator == (const ahbRespSt< D > & rhs) const {
        return (
            rhs.hrdata == hrdata &&
            rhs.hresp == hresp
        );
    }
    inline friend void sc_trace(sc_trace_file *tf, const ahbRespSt< D > & v, const std::string & NAME ) {
        sc_trace(tf,v.hrdata, NAME + ".hrdata");
        sc_trace(tf,v.hresp, NAME + ".hresp");
    }
    inline friend ostream& operator << ( ostream& os, ahbRespSt< D > const & v ) {
        os << "("
           << v.hrdata.prt() << ", "
           << (v.hresp ? "ERROR" : "OKAY") << ");";
        return os;
    }
    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        ss << "hrdata:" << hrdata.prt()
           << " hresp:" << (hresp ? "ERROR" : "OKAY");
        return(ss.str());
    }
    static const char * getValueType(void)
    {
        return( D::getValueType() );
    }
    inline uint64_t getStructValue(void) const
    {
        return( hrdata.getStructValue() );
    }
    inline void pack(_packedSt &_ret) const
    {
        uint16_t _pos{0};
        memset(&_ret, 0, ahbRespSt::_byteWidth);
        pack_payload_bits((uint64_t *)&_ret, _pos, hrdata, dataWidth);
        _pos += dataWidth;
        pack_bits((uint64_t *)&_ret, _pos, hresp, respWidth);
        _pos += respWidth;
    }
    inline void unpack(_packedSt &_src)
    {
        uint16_t _pos{0};
        unpack_payload_bits(hrdata, _src, _pos, dataWidth);
        _pos += dataWidth;
        unpack_scalar_bits(hresp, _src, _pos, respWidth);
        _pos += respWidth;
    }

};

template <class A, class D>
class ahb_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // subordinate interfaces
    virtual void receiveAddr( ahbAddrSt<A>& ) = 0;
    virtual void receiveData( D& ) = 0; // write data, once per write in address order
    virtual void sendResp( const ahbRespSt<D>& ) = 0; // completes the oldest data phase
    // arbitration: reflects the address sub-channel, since the arbitration
    // decision on the dst side is made at the address phase
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    ahb_in_if()
        {}

private:
    // disabled
    ahb_in_if( const ahb_in_if<A, D>& );
    ahb_in_if<A, D>& operator = ( const ahb_in_if<A, D>& );
};


template <class A, class D>
class ahb_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // manager interfaces
    virtual void sendAddr( const ahbAddrSt<A>&, std::optional<std::string> str=std::nullopt ) = 0;
    virtual void sendData( const D& ) = 0; // write data, once per write in address order, waits for the write's sendAddr
    virtual void receiveResp( ahbRespSt<D>& ) = 0; // response of the oldest data phase

protected:
    // constructor
    ahb_out_if()
        {}

private:
    // disabled
    ahb_out_if( const ahb_out_if<A, D>& );
    ahb_out_if<A, D>& operator = ( const ahb_out_if<A, D>& );
};

class ahb_transaction_counter {
public:
    inline static uint64_t transactionNo{0};
};

template <class A, class D>
class ahb_channel
: public ahb_in_if<A, D>,
  public ahb_out_if<A, D>,
  public sc_prim_channel,
  public ahb_transaction_counter
{
public:
    // constructor const char * module, std::string block
    explicit ahb_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        m_addr_channel((std::string(name_) + "addr").c_str(), block_, BACKPRESSURE_ALLOWED),
        m_data_channel((std::string(name_) + "data").c_str(), block_, BACKPRESSURE_ALLOWED),
        m_resp_channel((std::string(name_) + "resp").c_str(), block_, BACKPRESSURE_ALLOWED),
        m_addr_out((std::string(name_) + "addrOut").c_str()),
        m_data_out((std::string(name_) + "dataOut").c_str()),
        m_resp_out((std::string(name_) + "respOut").c_str()),
        m_addr_in((std::string(name_) + "addrIn").c_str()),
        m_data_in((std::string(name_) + "dataIn").c_str()),
        m_resp_in((std::string(name_) + "respIn").c_str()),
        m_reader(nullptr),
        m_writer(nullptr),
        m_logQueueAddr(std::make_shared<stringPingPong>()),
        m_logQueueData(std::make_shared<stringPingPong>()),
        m_logQueueResp(std::make_shared<stringPingPong>())
        {
            m_addr_in( m_addr_channel );
            m_addr_out( m_addr_channel );
            m_data_in( m_data_channel );
            m_data_out( m_data_channel );
            m_resp_in( m_resp_channel );
            m_resp_out( m_resp_channel );
            m_addr_channel.setLogQueue(m_logQueueAddr);
            m_data_channel.setLogQueue(m_logQueueData);
            m_resp_channel.setLogQueue(m_logQueueResp);
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~ahb_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // out interfaces
    virtual void sendAddr( const ahbAddrSt<A>&, std::optional<std::string> str ) override;
    virtual void sendData( const D& ) override;
    virtual void receiveResp( ahbRespSt<D>& ) override;

    // in interfaces
    virtual void receiveAddr( ahbAddrSt<A>& ) override;
    virtual void receiveData( D& ) override;
    virtual void sendResp( const ahbRespSt<D>& ) override;
    virtual bool isActive() override { return m_addr_in->isActive(); }
    virtual bool isNotActive() override { return m_addr_in->isNotActive(); }
    virtual void setExternalEvent( sc_event *event ) override { m_addr_in->setExternalEvent(event); }

    // other methods
    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "ahb_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        Q_ASSERT(false, std::format("multiple drivers on {} ahb interface is invalid", name_ ));
    }
    // every transfer, read or write, ends on the response sub-channel
    std::shared_ptr<trackerBase> getTracker(void) override { return (m_resp_in->getTracker());}
    virtual void setTeeBusy(bool busy) override { m_resp_in->setTeeBusy(busy); }
    virtual void setTandem(void) override { m_addr_channel.setTandem(); m_data_channel.setTandem(); m_resp_channel.setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { m_addr_channel.setLogging(verbosity); m_data_channel.setLogging(verbosity); m_resp_channel.setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { m_addr_channel.setTimed(nsec, mode); m_data_channel.setTimed(nsec, mode); m_resp_channel.setTimed(nsec, mode); }
    virtual sc_prim_channel* getChannel(void) override { return this; }
protected:
    rdy_vld_channel<ahbAddrSt<A>> m_addr_channel;
    rdy_vld_channel<D> m_data_channel;
    rdy_vld_channel<ahbRespSt<D>> m_resp_channel;
public: // make these public for the tees/verif
    rdy_vld_out <ahbAddrSt<A>> m_addr_out; // for sending address (ahb_out)
    rdy_vld_out <D> m_data_out; // for sending write data (ahb_out)
    rdy_vld_out <ahbRespSt<D>> m_resp_out; // for sending response (ahb_in)
    rdy_vld_in <ahbAddrSt<A>> m_addr_in; // for receiving address (ahb_in)
    rdy_vld_in <D> m_data_in; // for receiving write data (ahb_in)
    rdy_vld_in <ahbRespSt<D>> m_resp_in; // for receiving response (ahb_out)

protected:
    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

private:
    std::queue<_ahb_transfer_st> m_data_transfers; // writes waiting for sendData, in address order
    sc_event m_write_addr_event; // a write joined m_data_transfers
    std::queue<_ahb_transfer_st> m_resp_transfers; // transfers waiting for sendResp, in address order
    // disabled
    ahb_channel( const ahb_channel<A, D>& );
    ahb_channel& operator = ( const ahb_channel<A, D>& );
    std::shared_ptr<stringPingPong> m_logQueueAddr;
    std::shared_ptr<stringPingPong> m_logQueueData;
    std::shared_ptr<stringPingPong> m_logQueueResp;
    void pushTransactionLog(interfaceBase &ifb, std::shared_ptr<stringPingPong> &queue, const _ahb_transfer_st &txn);
};

template <class A, class D>
inline void ahb_channel<A, D>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( ahb_in_if<A, D> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( ahb_out_if<A, D> ).name() )
    {
        // only one writer can be connected
        if( m_writer != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_WRITER_, 0 );
            // may continue, if suppressed
        }
        m_writer = &port_;
    }
    else
    {
        SC_REPORT_ERROR( SC_ID_BIND_IF_TO_PORT_,
                         "ahb_channel<A, D> port not recognized" );
        // may continue, if suppressed
    }
}

template <class A, class D>
inline void ahb_channel<A, D>::pushTransactionLog(interfaceBase &ifb, std::shared_ptr<stringPingPong> &queue, const _ahb_transfer_st &txn)
{
    if (ifb.log_.isMatch(LOG_NORMAL)) {
        if (txn.transactionStr) {
            queue->push(*txn.transactionStr);
        } else {
            queue->push(std::format("HTX#{:x} ", txn.transactionNo));
        }
    }
}

template <class A, class D>
inline void ahb_channel<A, D>::sendAddr( const ahbAddrSt<A>& addr_, std::optional<std::string> str )
{
    // IDLE and BUSY carry no transfer, so they stay on the pins.
    Q_ASSERT(addr_.htrans == AHBTRANS_NONSEQ || addr_.htrans == AHBTRANS_SEQ, "ahb sendAddr htrans must be NONSEQ or SEQ");
    _ahb_transfer_st txn{addr_.hwrite, transactionNo++, std::move(str)};
    pushTransactionLog(m_addr_channel, m_logQueueAddr, txn);
    if (txn.write) {
        m_data_transfers.push(txn);
        m_write_addr_event.notify();
    }
    m_resp_transfers.push(std::move(txn));
    m_addr_out->write(addr_);
}

template <class A, class D>
inline void ahb_channel<A, D>::sendData( const D& data_ )
{
    // A manager may run its data phase on its own thread, so the write data can
    // arrive before its address.
    while (m_data_transfers.empty()) {
        wait(m_write_addr_event);
    }
    pushTransactionLog(m_data_channel, m_logQueueData, m_data_transfers.front());
    m_data_transfers.pop();
    m_data_out->write(data_);
}

template <class A, class D>
inline void ahb_channel<A, D>::receiveResp( ahbRespSt<D>& resp_ )
{
    m_resp_in->read(resp_);
}

template <class A, class D>
inline void ahb_channel<A, D>::receiveAddr( ahbAddrSt<A> &addr_ )
{
    m_addr_in->read(addr_);
}

template <class A, class D>
inline void ahb_channel<A, D>::receiveData( D &data_ )
{
    m_data_in->read(data_);
}

template <class A, class D>
inline void ahb_channel<A, D>::sendResp( const ahbRespSt<D>& resp_ )
{
    if (m_resp_transfers.empty()) {
        m_resp_channel.log_.logPrint(std::format("response without an address: {}", resp_.prt()));
        Q_ASSERT(false, "ahb sendResp without an address");
    }
    pushTransactionLog(m_resp_channel, m_logQueueResp, m_resp_transfers.front());
    m_resp_transfers.pop();
    m_resp_out->write(resp_);
}

template <class A, class D>
void ahb_channel<A, D>::status(void)
{
    if (!m_resp_transfers.empty()) {
        m_resp_channel.log_.logPrint(
            std::format("{} has {} transfers without a response, {} writes without data",
                        name(), m_resp_transfers.size(), m_data_transfers.size()),
            LOG_IMPORTANT);
    }
}

template <class A, class D>
inline void ahb_channel<A, D>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class A, class D>
inline void ahb_channel<A, D>::print( ::std::ostream& os ) const
{
    m_addr_channel.print(os);
    m_data_channel.print(os);
    m_resp_channel.print(os);
}

template <class A, class D>
inline void ahb_channel<A, D>::dump( ::std::ostream& os ) const
{

}

template <class A, class D>
inline ::std::ostream& operator << ( ::std::ostream& os, const ahb_channel<A, D>& a )
{
    a.print( os );
    return os;
}

template <class A, class D>
using ahb_out = sc_port<ahb_out_if<A, D> >;
template <class A, class D>
using ahb_in = sc_port<ahb_in_if<A, D> >;

#endif // AHB_CHANNEL_H
