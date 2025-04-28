// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_CHANNEL_H
#define AXI_WRITE_CHANNEL_H

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

// sendAddr( A )
//          -------> receiveAddr( &A )
// sendData( D )
//          -------> receiveData( &D )
//
//                   sendResp( S )
// receiveResp( &S ) <-------

template <typename D, typename S>
struct axiWriteDataSt
{
    _axiIdT wid; // Write ID tag. This signal is the identification tag for the write data group of signals
    D wdata;     // Write data
    S wstrb;     // Write strobes. This signal indicates which byte lanes hold valid data
    bool wlast;  // Write last. This signal indicates the last transfer in a write burst transaction
    static constexpr int idWidth = 4; // number of bits in wid
    static constexpr int dataWidth = D::_bitWidth; // number of bits in wdata
    static constexpr int strbWidth = S::_bitWidth; // number of bits in wstrb
    axiWriteDataSt() {};

    static int getBurstSize(void) { return(sizeof(D));} // returns datapath width in bytes

    inline D * getDataPtr(void) {return &wdata;} // returns pointer to internal data element. Note this is unrelated to any backdoor

    inline bool operator == (const axiWriteDataSt< D, S > & rhs) const {
        return (
            rhs.wid == wid &&
            rhs.wdata == wdata &&
            rhs.wstrb == wstrb &&
            rhs.wlast == wlast
        );
    }
    inline friend void sc_trace(sc_trace_file *tf, const axiWriteDataSt< D, S > & v, const std::string & NAME ) {
        sc_trace(tf,v.wid, NAME + ".wid");
        sc_trace(tf,v.wdata, NAME + ".wdata");
        sc_trace(tf,v.wstrb, NAME + ".rresp");
        sc_trace(tf,v.wlast, NAME + ".rlast");
    }
    inline friend ostream& operator << ( ostream& os,  axiWriteDataSt< D, S > const & v ) {
        os << "("
           << std::hex << std::setw(1) << (int)v.wid << ", "
           << v.wdata.prt() << ", "
           << v.wstrb.prt() << ", "
           << std::hex << std::setw(1) << (int)v.wlast << ");";
        return os;
    }
    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        ss << "wid:0x" << std::hex << std::setw(1) << (int)wid
           << " wdata:" << wdata.prt()
           << " wstrb:" << wstrb.prt()
           << " wlast:0x" << std::hex << std::setw(1) << (int)wlast;
        return(ss.str());
    }
    static const char * getValueType(void)
    {
        return( D::getValueType() );
    }
    inline uint64_t getStructValue(void) const
    {
        return( wdata.getStructValue() );
    }

};

template <typename A>
struct axiWriteAddressSt
{
    _axiIdT     awid;    // Write address ID. This signal is the identification tag for the write address group of signals (4bits)
    A           awaddr;  // Write address. The write address gives the address of the first transfer in a write burst transaction
    uint8_t     awlen;   // Burst length. This signal indicates the exact number of transfers in a burst.
    _axiSizeT   awsize;  // Burst size. This signal indicates the size of each transfer in the burst.
    _axiBurstT  awburst; // Master Burst type. The burst type and the size information determine how the address for each transfer within the burst is calculated
    static constexpr int idWidth = 4; // number of bits in awid
    static constexpr int addrWidth = A::_bitWidth; // number of bits in awaddr
    static constexpr int lenWidth = 8; // number of bits in awlen
    static constexpr int sizeWidth = 3; // number of bits in awsize
    static constexpr int burstWidth = 2; // number of bits in awburst

    axiWriteAddressSt() {};

    inline bool operator == (const axiWriteAddressSt< A > & rhs) const {
        return (
            rhs.awid == awid &&
            rhs.awaddr == awaddr &&
            rhs.awlen == awlen &&
            rhs.awsize == awsize &&
            rhs.awburst == awburst
        );
    }
    inline friend void sc_trace(sc_trace_file *tf, const axiWriteAddressSt< A > & v, const std::string & NAME ) {
        sc_trace(tf,v.awid, NAME + ".awid");
        sc_trace(tf,v.awaddr, NAME + ".awaddr");
        sc_trace(tf,v.awlen, NAME + ".awlen");
        sc_trace(tf,v.awsize, NAME + ".awsize");
        sc_trace(tf,v.awburst, NAME + ".awburst");
    }
    inline friend ostream& operator << ( ostream& os, axiWriteAddressSt< A > const & v ) {
        os << "("
           << (int)v.awid << ", "
           << v.awaddr.prt() << ", "
           << (int)v.awlen << ", "
           << (int)v.awsize << ", "
           << _axiBurstT_prt(v.awburst) << ");";
        return os;
    }
    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        ss << "awid:0x" << std::hex << std::setw(1) << (int)awid
           << " awaddr:" << awaddr.prt()
           << " awlen:0x" << std::hex << std::setw(2) << std::setfill('0') << (int)awlen
           << " awsize:0x" << std::hex << std::setw(1) << (int)awsize
           << " awburst:" << _axiBurstT_prt(awburst);
        return(ss.str());
    }
    static const char * getValueType(void)
    {
        return( A::getValueType() );
    }
    inline uint64_t getStructValue(void) const
    {
        return( awaddr.getStructValue() );
    }

};

struct axiWriteRespSt
{
    _axiIdT     bid;    // Write address ID. This signal is the identification tag for the write address group of signals (4bits)
    _axiResponseT bresp; // Write response. This signal indicates the status of the write transaction
    static constexpr int idWidth = 4; // number of bits in bid
    static constexpr int respWidth = 2; // number of bits in bresp

    axiWriteRespSt() {};

    inline bool operator == (const axiWriteRespSt & rhs) const {
        return (
            rhs.bid == bid &&
            rhs.bresp == bresp
        );
    }
    inline friend void sc_trace(sc_trace_file *tf, const axiWriteRespSt & v, const std::string & NAME ) {
        sc_trace(tf,v.bid, NAME + ".bid");
        sc_trace(tf,v.bresp, NAME + ".bresp");
    }
    inline friend ostream& operator << ( ostream& os, axiWriteRespSt const & v ) {
        os << "("
           << (int)v.bid << ", "
           << _axiResponseT_prt(v.bresp) << ");";
        return os;
    }
    std::string prt(bool all=false) const
    {
        std::stringstream ss;
        ss << "bid:0x" << std::hex << std::setw(1) << (int)bid
           << " bresp:" << _axiResponseT_prt(bresp);
        return(ss.str());
    }
    static const char * getValueType(void)
    {
        return( "" );
    }
    inline uint64_t getStructValue(void) const
    {
        return( -1 );
    }

};

template <class A, class D, class S>
class axi_write_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // receiver interfaces
    virtual void receiveAddr( axiWriteAddressSt<A>& ) = 0;
    virtual void receiveData( axiWriteDataSt<D, S>& ) = 0;
    virtual void receiveDataCycle(  axiWriteDataSt<D, S>& ) = 0;  // for multi cycle channels, gets one burst
    virtual void sendResp( const axiWriteRespSt& ) = 0;
    virtual void sendRespCycle( const axiWriteRespSt& ) = 0;
    virtual void push_burst(uint32_t burstCount) = 0; // push number of burst
    virtual uint8_t * getReceiveDataPtr(void) = 0;

protected:
    // constructor
    axi_write_in_if()
        {}

private:
    // disabled
    axi_write_in_if( const axi_write_in_if<A, D, S>& );
    axi_write_in_if<A, D, S>& operator = ( const axi_write_in_if<A, D, S>& );
};


template <class A, class D, class S>
class axi_write_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // sender interfaces
    virtual void sendAddr( const axiWriteAddressSt<A>&, std::optional<std::string> str=std::nullopt ) = 0;
    virtual void sendData( const axiWriteDataSt<D, S>& ) = 0;
    virtual void sendData( const axiWriteDataSt<D, S>&, int burstCount ) = 0;
    virtual void sendDataCycle( const axiWriteDataSt<D, S>& ) = 0;
    virtual void receiveResp( axiWriteRespSt& ) = 0;
    virtual void receiveRespCycle( axiWriteRespSt& ) = 0;
    virtual uint8_t * getSendDataPtr(void) = 0;

protected:
    // constructor
    axi_write_out_if()
        {}

private:
    // disabled
    axi_write_out_if( const axi_write_out_if<A, D, S>& );
    axi_write_out_if<A, D, S>& operator = ( const axi_write_out_if<A, D, S>& );
};

class axi_write_transaction_counter {
public:
    inline static uint64_t transactionNo{0};
};


template <class A, class D, class S>
class axi_write_channel
: public axi_write_in_if<A, D, S>,
  public axi_write_out_if<A, D, S>,
  public sc_prim_channel,
  public axi_write_transaction_counter
{
public:
    // constructor const char * module, std::string block
    explicit axi_write_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        m_addr_channel((std::string(name_) + "addr").c_str(), block_),
        m_data_channel((std::string(name_) + "data").c_str(), block_),
        m_resp_channel((std::string(name_) + "resp").c_str(), block_),
        m_addr_out((std::string(name_) + "addrOut").c_str()),
        m_data_out((std::string(name_) + "dataOut").c_str()),
        m_resp_out((std::string(name_) + "respOut").c_str()),
        m_addr_in((std::string(name_) + "addrIn").c_str()),
        m_data_in((std::string(name_) + "dataIn").c_str()),
        m_resp_in((std::string(name_) + "respIn").c_str()),
        m_reader(nullptr),
        m_writer(nullptr),
        m_resp_transactions(AXI_TRANSACTION_ID_MAX),
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
        }

    explicit axi_write_channel( const char* name_, std::string block_, std::string multiCycleType_, int pingpong_size_, std::string trackerName_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        m_addr_channel((std::string(name_) + "addr").c_str(), block_),
        m_data_channel((std::string(name_) + "data").c_str(), block_, multiCycleType_, pingpong_size_*sizeof(axiWriteDataSt<D, S>), trackerName_),
        m_resp_channel((std::string(name_) + "resp").c_str(), block_),
        m_addr_out((std::string(name_) + "addrOut").c_str()),
        m_data_out((std::string(name_) + "dataOut").c_str()),
        m_resp_out((std::string(name_) + "respOut").c_str()),
        m_addr_in((std::string(name_) + "addrIn").c_str()),
        m_data_in((std::string(name_) + "dataIn").c_str()),
        m_resp_in((std::string(name_) + "respIn").c_str()),
        m_reader(nullptr),
        m_writer(nullptr),
        m_resp_transactions(AXI_TRANSACTION_ID_MAX),
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
            Q_ASSERT(multiCycleType_ =="" || multiCycleType_ == "api_list_size" || multiCycleType_ == "fixed_size", "multiCycleType must be api_list_size or fixed_size");
            m_addr_channel.setLogQueue(m_logQueueAddr);
            m_data_channel.setLogQueue(m_logQueueData);
            m_resp_channel.setLogQueue(m_logQueueResp);
        }

    // destructor
    virtual ~axi_write_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // out interfaces
    virtual void sendAddr( const axiWriteAddressSt<A>&, std::optional<std::string> str ) override;
    virtual void sendData( const axiWriteDataSt<D, S>& ) override;
    virtual void sendData( const axiWriteDataSt<D, S>&, int burstCount ) override;
    virtual void sendDataCycle( const axiWriteDataSt<D, S>& ) override;
    virtual void receiveResp( axiWriteRespSt& ) override;
    virtual void receiveRespCycle( axiWriteRespSt& ) override;
    virtual uint8_t * getSendDataPtr( void ) override    { return m_data_out->getWritePtr();}

    // in interfaces
    virtual void receiveAddr( axiWriteAddressSt<A>& ) override;
    virtual void receiveData( axiWriteDataSt<D, S>& ) override;
    virtual void receiveDataCycle( axiWriteDataSt<D, S>& ) override;
    virtual void sendResp( const axiWriteRespSt& ) override;
    virtual void sendRespCycle( const axiWriteRespSt& ) override;
    virtual void push_burst(uint32_t burstCount) override
    {
        m_data_in->push_context(burstCount * sizeof(axiWriteDataSt<D, S>));
    }
    virtual uint8_t * getReceiveDataPtr(void) override { return m_data_in->getReadPtr(); }

    // other methods
    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "axi_write_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        Q_ASSERT(false, fmt::format("multiple drivers on {} axiWr interface is invalid", name_ ));
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (m_data_in->getTracker());}
    virtual void setTeeBusy(bool busy) override { m_data_in->setTeeBusy(busy); }
    virtual void setTandem(void) override { m_addr_channel.setTandem(); m_data_channel.setTandem(); m_resp_channel.setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { m_addr_channel.setLogging(verbosity); m_data_channel.setLogging(verbosity); m_resp_channel.setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { m_addr_channel.setTimed(nsec, mode); m_data_channel.setTimed(nsec, mode); m_resp_channel.setTimed(nsec, mode);}
    virtual void setCycleTransaction(portType type_) override
    {
        Q_ASSERT(type_ != PORTTYPE_ANY, "For AXI read, PORTTYPE_SOURCE or PORTTYPE_DEST must be specified");
        // axi in = axi_resp = data out
        if (type_ == PORTTYPE_IN) {
            m_receiver_cycle_transaction = true;
            m_data_out->setCycleTransaction();
        }
        // axi out = axi_req = data in
        if (type_ == PORTTYPE_OUT) {
            m_sender_cycle_transaction = true;
            m_data_in->setCycleTransaction();
         }
    }
protected:
    rdy_vld_channel<axiWriteAddressSt<A>> m_addr_channel;
    rdy_vld_channel<axiWriteDataSt<D, S>> m_data_channel;
    rdy_vld_channel<axiWriteRespSt> m_resp_channel;
public: // make these public for the tees/verif
    rdy_vld_out <axiWriteAddressSt<A>> m_addr_out; // for sending address (axi_out)
    rdy_vld_out <axiWriteDataSt<D, S>> m_data_out; // for sending data (axi_out)
    rdy_vld_out <axiWriteRespSt> m_resp_out; // for sending response (axi_in)
    rdy_vld_in <axiWriteAddressSt<A>> m_addr_in; // for receiving address (axi_in)
    rdy_vld_in <axiWriteDataSt<D, S>> m_data_in; // for receiving data (axi_in)
    rdy_vld_in <axiWriteRespSt> m_resp_in; // for receiving response (axi_out)

protected:
    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

private:
    sc_event m_address_synch_event;
    std::queue<_axi_transaction_st> m_send_transactions; // queue of transactions by transaction id per axi
    bool m_send_transaction_are_addr = true;
    std::vector<std::queue<_axi_transaction_st>> m_resp_transactions; // queue of transactions by transaction id per axi
    _axi_transaction_st m_current_send_data_transaction;
    _axi_transaction_st m_current_send_resp_transaction;
    bool m_sender_cycle_transaction = false;
    bool m_receiver_cycle_transaction = false;
    bool m_data_sender_new_transaction = true;
    // disabled
    axi_write_channel( const axi_write_channel<A, D, S>& );
    axi_write_channel& operator = ( const axi_write_channel<A, D, S>& );
    std::shared_ptr<stringPingPong> m_logQueueAddr;
    std::shared_ptr<stringPingPong> m_logQueueData;
    std::shared_ptr<stringPingPong> m_logQueueResp;
    void manageSendDataTransaction(const axiWriteDataSt<D, S> & data_);
    void handleSendTransactionLog(void);
    void manageSendRespTransaction(const axiWriteRespSt & data_);
    void handleSendRespTransactionLog(void);
};

template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( axi_write_in_if<A, D, S> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( axi_write_out_if<A, D, S> ).name() )
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
                         "axi_write_channel<A, D, S> port not recognized" );
        // may continue, if suppressed
    }
}
template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::manageSendDataTransaction(const axiWriteDataSt<D, S> & data_)
{
    if (m_send_transactions.empty() || !m_send_transaction_are_addr) {
        // if there are no transactions in the queue, then data is first so create a new transaction
        m_current_send_data_transaction = _axi_transaction_st(0, 0, 0, transactionNo++, std::nullopt);
        m_send_transactions.emplace(m_current_send_data_transaction);
        m_send_transaction_are_addr = false;
    } else {
        // addr is first so use the transaction from the queue and push to the response queue
        m_current_send_data_transaction = m_send_transactions.front();
        Q_ASSERT(m_current_send_data_transaction.id == data_.wid, "transaction id not valid");
        m_send_transactions.pop();
        m_resp_transactions[m_current_send_data_transaction.id].emplace(m_current_send_data_transaction);
    }
}
template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::handleSendTransactionLog(void)
{
    if (m_data_channel.log_.isMatch(LOG_NORMAL)) {
        if (m_current_send_data_transaction.transactionStr) {
            m_logQueueData->push(*m_current_send_data_transaction.transactionStr);
        } else {
            m_logQueueData->push(fmt::format("WTX#{:x} ",m_current_send_data_transaction.transactionNo));
        }
    }

}
template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::manageSendRespTransaction(const axiWriteRespSt & resp_)
{
    if (m_resp_transactions[resp_.bid].empty()) {
        m_resp_channel.log_.logPrint(fmt::format("transaction id not valid: {}", resp_.prt()));
        Q_ASSERT(false, "transaction id not valid");
    }
    m_current_send_resp_transaction = m_resp_transactions[resp_.bid].front();
    m_resp_transactions[resp_.bid].pop();
}
template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::handleSendRespTransactionLog(void)
{
    if (m_resp_channel.log_.isMatch(LOG_NORMAL)) {
        if (m_current_send_resp_transaction.transactionStr) {
            m_logQueueResp->push(*m_current_send_resp_transaction.transactionStr);
        } else {
            m_logQueueResp->push(fmt::format("WTX#{:x} ",m_current_send_resp_transaction.transactionNo));
        }
    }
}

// blocking transactional read
template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::receiveAddr( axiWriteAddressSt<A> &addr_ )
{
    m_addr_in->read(addr_);
}

template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::receiveData( axiWriteDataSt<D, S> &data_ )
{
    m_data_in->read(data_);
}


template <class A, class D, class S>
void axi_write_channel<A, D, S>::receiveDataCycle(  axiWriteDataSt<D, S> & data_)
{
    m_data_in->readClocked(data_);
}

template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::sendAddr( const axiWriteAddressSt<A>& addr_, std::optional<std::string> str )
{
    uint64_t txn;
    if (m_send_transactions.empty() || m_send_transaction_are_addr) {
        // if there are no transactions in the queue, then address is first so create a new transaction
        txn = transactionNo++;
        m_send_transactions.emplace(addr_.awid, addr_.awlen, addr_.awsize, txn, std::move(str));
        m_send_transaction_are_addr = true;
    } else {
        // data is first so use the transaction from the queue and push to the response queue
        txn = m_send_transactions.front().transactionNo; // data only fills the transaction number
        m_send_transactions.pop();
        m_resp_transactions[addr_.awid].emplace(addr_.awid, addr_.awlen, addr_.awsize, txn, std::move(str));
    }
    if (m_addr_channel.log_.isMatch(LOG_NORMAL)) {
        if (str) {
            m_logQueueAddr->push(*str);
        } else {
            m_logQueueAddr->push(fmt::format("WTX#{:x} ",txn));
        }
    }
    if (m_sender_cycle_transaction && !m_receiver_cycle_transaction) {
        // as the sender is cycle based we need to pretend that the reader is providing the context for the multicycle data transfer
        m_data_in->push_context((addr_.awlen + 1) * sizeof(axiWriteDataSt<D, S>));
        m_address_synch_event.notify(); // incase the sender is waiting for the address
    }
    m_addr_out->write(addr_);
}

template <class A, class D, class S>
void axi_write_channel<A, D, S>::sendData( const axiWriteDataSt<D, S>& data_ )
{
    manageSendDataTransaction(data_);
    handleSendTransactionLog();
    m_data_out->write(data_);
}
template <class A, class D, class S>
void axi_write_channel<A, D, S>::sendData( const axiWriteDataSt<D, S>& data_, int burstCount )
{
    manageSendDataTransaction(data_);
    handleSendTransactionLog();
    m_data_out->write(data_, burstCount * sizeof(axiWriteDataSt<D, S>));
}


template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::sendDataCycle( const axiWriteDataSt<D, S>& data_)
{
    if (!m_receiver_cycle_transaction && m_data_sender_new_transaction) {
        // receiver is not cycle based, so we must enforce addr before data
        if (m_send_transactions.empty()) {
            // for the case of sender clocked and receiver transactional, we need to wait for address
            // otherwise we have no size context to use the interface
            wait(m_address_synch_event);
        }

    }
    if (m_data_sender_new_transaction) {
        manageSendDataTransaction(data_);
        m_data_sender_new_transaction = false;
    }

    if (data_.wlast) {
        // next cycle will be a new transaction
        m_data_sender_new_transaction = true;
    }

    handleSendTransactionLog();
    m_data_out->writeClocked(data_);
}

template <class A, class D, class S>
void axi_write_channel<A, D, S>::sendResp( const axiWriteRespSt& resp_ )
{
    manageSendRespTransaction(resp_);
    handleSendRespTransactionLog();
    m_resp_out->write(resp_);
}


template <class A, class D, class S>
void axi_write_channel<A, D, S>::sendRespCycle( const axiWriteRespSt& resp_)
{
    sendResp(resp_);
}

template <class A, class D, class S>
void axi_write_channel<A, D, S>::receiveResp( axiWriteRespSt& resp_)
{
    m_resp_in->read(resp_);
}

template <class A, class D, class S>
void axi_write_channel<A, D, S>::receiveRespCycle( axiWriteRespSt& resp_)
{
    receiveResp(resp_);
}


template <class A, class D, class S>
void axi_write_channel<A, D, S>::status(void)
{
    // nothing useful yet, as internal interfaces will give their own status
    //teeStatus();
}

template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::print( ::std::ostream& os ) const
{
    m_addr_channel.print(os);
    m_data_channel.print(os);
}

template <class A, class D, class S>
inline void axi_write_channel<A, D, S>::dump( ::std::ostream& os ) const
{

}

template <class A, class D, class S>
inline ::std::ostream& operator << ( ::std::ostream& os, const axi_write_channel<A, D, S>& a )
{
    a.print( os );
    return os;
}

template <class A, class D, class S>
using axi_write_out = sc_port<axi_write_out_if<A, D, S> >;
template <class A, class D, class S>
using axi_write_in = sc_port<axi_write_in_if<A, D, S> >;

#endif // AXI_WRITE_CHANNEL_H
