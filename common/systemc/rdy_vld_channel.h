// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef RDY_VLD_CHANNEL_H
#define RDY_VLD_CHANNEL_H

#include "sysc/communication/sc_communication_ids.h"
#include "sysc/communication/sc_prim_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/tracing/sc_trace.h"
#include <typeinfo>
#include <iostream>
#include "portBase.h"
#include "interfaceBase.h"
#include "multiCycleBase.h"
#include "pingPongBuffer.h"
#include "synchLock.h"
#include <format>

namespace sc_core {

// write( T )
//          ----T---> read( &T )

template <class T>
class rdy_vld_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void read( T& ) = 0;
    virtual T read() = 0;
    virtual void readClocked( T& ) = 0;  // for multi cycle channels, gets one burst
    virtual uint8_t * getReadPtr(void) = 0;
    virtual int getReadCycle(void) = 0;
    virtual void set_rdy(bool) = 0;
    virtual bool get_rdy() const = 0;
    virtual void enable_user_ready_control(void) = 0;
    virtual void push_context(uint32_t) = 0;
    virtual uint32_t get_context(void) = 0;
    virtual uint32_t get_max_size(void) = 0;
    virtual void setTimedDelayPtr(std::shared_ptr<timedDelayBase> pTimedDelay) = 0;

protected:
    // constructor
    rdy_vld_in_if()
        {}

private:
    // disabled
    rdy_vld_in_if( const rdy_vld_in_if<T>& );
    rdy_vld_in_if<T>& operator = ( const rdy_vld_in_if<T>& );
};


template <class T>
class rdy_vld_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking write
    virtual void write( const T& ) = 0;
    virtual void write( const T&, int buffer_size ) = 0;
    virtual void writeClocked( const T& ) = 0;
    virtual int getWriteCycle(void) = 0;
    virtual std::shared_ptr<trackerBase> getTracker(void) = 0;
    virtual uint8_t * getWritePtr(void) = 0;
    virtual bool get_rdy() const = 0;
    virtual void setTimedDelayPtr(std::shared_ptr<timedDelayBase> pTimedDelay) = 0;

protected:
    // constructor
    rdy_vld_out_if()
        {}

private:
    // disabled
    rdy_vld_out_if( const rdy_vld_out_if<T>& );
    rdy_vld_out_if<T>& operator = ( const rdy_vld_out_if<T>& );
};

template <class T>
class rdy_vld_channel
: public rdy_vld_in_if<T>,
  public rdy_vld_out_if<T>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit rdy_vld_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_sync_event( (std::string(name_) + "m_channel_sync_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_burst_size(sizeof(T)),
        m_pingpong_size(0)
        {
            setTracker(T::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    explicit rdy_vld_channel( const char* name_, std::string block_, std::string multiCycleType_, int pingpong_size_, std::string trackerName_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_sync_event( (std::string(name_) + "m_channel_sync_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_burst_size(sizeof(T)),
        m_pingpong_size(pingpong_size_),
        m_multicycle(multiCycleFactory::createMultiCycle(std::string(name_), multiCycleType_, sizeof(T), pingpong_size_, trackerName_))
        {
            std::string trackerString(T::getValueType());
            if (trackerString == "") {
                trackerString = trackerName_;
            }
            setTracker(trackerString.c_str());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
            if (multiCycleType_ == "api_list_tracker" ) {
                m_get_struct_value = false; // we are using a tracker but the value comes from api/list
            }
            if (multiCycleType_ == "api_list_tracker" || multiCycleType_ == "api_list_size" ) {
                m_tee_handle_context = true;
            }
            if (multiCycleType_ == "fixed_size" || multiCycleType_ == "api_list_size" ) {
                // ping pong cases
                m_tee_handle_copy = true;
            }
        }

    // destructor
    virtual ~rdy_vld_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // blocking read
    virtual void read( T& ) override;
    virtual T read() override;
    virtual void readClocked( T& ) override;
    virtual int getReadCycle(void) override
    {
        if (m_multicycle == nullptr) {
            return 0;
        }
        return m_multicycle->getReadCycle();
    }
    virtual uint8_t * getReadPtr( void ) override;
    virtual void push_context(uint32_t size) override { m_multicycle->push_context(size); }
    virtual void set_rdy(bool rdy_state) override
    {
        m_ready = rdy_state;
        sc_prim_channel::request_update();
    }
    virtual void enable_user_ready_control(void) override
    {
        m_user_ready_control = true;
    }
    virtual uint32_t get_context(void) override
    {
        if (m_tee_handle_context) {
            return m_read_context;
        } else {
            Q_ASSERT(false, "get_context not supported");
            return (uint32_t)-1;
        }
    }
    virtual uint32_t get_max_size(void) override
    {
        return (uint32_t)m_pingpong_size;
    }

    // blocking write
    virtual void write( const T& ) override;
    void writeCore( const T& );
    virtual void write( const T&, int buffer_size ) override;
    virtual void writeClocked( const T& ) override;
    virtual int getWriteCycle(void) override
    {
        if (m_multicycle == nullptr) {
            return 0;
        }
        return m_multicycle->getWriteCycle();
    }
    virtual uint8_t * getWritePtr(void) override;

    virtual bool get_rdy() const override
    { return ( m_ready ); }

    // other methods
    operator T ()
    { return read(); }

    rdy_vld_channel<T>& operator = ( const T& a )
        { write( a ); return *this; }

    // compatability with sc_fifo
    int num_available(void) { return((int)m_valid);}

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "rdy_vld_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        Q_ASSERT(false, std::format("multiple drivers on {} rdyVld interface is invalid", name_));
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (tracker_);}
    virtual void setTeeBusy(bool busy) override { teeBusy_ = busy; }
    virtual void setTandem(void) override { interfaceBase::setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { interfaceBase::setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { interfaceBase::setTimed(nsec, mode); }
    virtual void setCycleTransaction(portType type_) override
    {
        cycleTransactionCount++;
        if (cycleTransactionCount > 1) {
            m_multicycle = nullptr;
            tracker_ = nullptr;
        }
    }
    virtual void setTimedDelayPtr(std::shared_ptr<timedDelayBase> pTimedDelay) override { interfaceBase::setTimedDelayPtr(pTimedDelay); }
    virtual void setLogQueue(std::shared_ptr<stringPingPong> logQueue) override { interfaceBase::setLogQueue(logQueue); }

protected:
    T    m_value;           // the data
    T    m_read_value;      // post transaction read value during clocking
    T    m_write_value;     // pre transaction write value during clocking

    sc_event m_channel_sync_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking
    bool m_ready = false;   // can we write the value
    bool m_valid = false;   // can we read the value
    bool m_value_written = false; // does m_value contain data not this is seperated from the ready/valid for optimization of the task switches
    bool m_wait_event = false;
    bool m_multi_writer = false;
    bool m_user_ready_control = false; // allow the user to externally control the ready state for verification use cases
    bool m_get_struct_value = true;
    bool m_tee_handle_context = false;
    bool m_tee_handle_copy = false;
    bool m_writer_waiting = false;
    int64_t m_write_context = -1;
    int64_t m_read_context = -1;
    const int m_burst_size;
    const int m_pingpong_size;
    int cycleTransactionCount = 0;
    std::unique_ptr<multiCycleBase> m_multicycle;

    // Primary channel override base class implementation
    void update() override {
        if (m_ready && m_valid) {
            m_valid = false;
            m_channel_sync_event.notify(SC_ZERO_TIME);
            if (m_multicycle != nullptr) {
                m_multicycle->update(); // perform implimentation specific actions eg flip the pingpong buffer
                m_read_context = m_write_context;
                m_write_context = -1;
            }
        }
    }

private:
    // disabled
    rdy_vld_channel( const rdy_vld_channel<T>& );
    rdy_vld_channel& operator = ( const rdy_vld_channel<T>& );
};

template <class T>
inline void rdy_vld_channel<T>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( rdy_vld_in_if<T> ).name() ) {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( rdy_vld_out_if<T> ).name() ) {
        // only one writer can be connected
        if( m_writer != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_WRITER_, 0 );
            // may continue, if suppressed
        }
        m_writer = &port_;
    } else {
        SC_REPORT_ERROR( SC_ID_BIND_IF_TO_PORT_,
                         "rdy_vld_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking read
template <class T>
inline void rdy_vld_channel<T>::read( T& val_ )
{
    bool logging = false;
    // if the user is not controlling the ready
    if (!m_user_ready_control) {
        m_ready = true;
    }
    sc_prim_channel::request_update();
    sc_core::wait(m_channel_sync_event);
    val_ = m_value;
    m_value_written = false;
    // if the user is not controlling the ready
    if (!m_user_ready_control) {
        m_ready = false;
    }
    int64_t tag;
    if (m_get_struct_value) {
        tag = val_.getStructValue();
    } else {
        tag = m_read_context;
    }
    if (m_multicycle == nullptr) {
        if (log_.isMatch(LOG_NORMAL)) {
            interfaceLog(val_.prt(isDebugLog), tag);
        }
    } else {
        // just get the first cycle to output to the log
        m_multicycle->copyReadData(tag, (uint8_t *)&val_);
        int buffer_size = m_multicycle->getReadBufferSize(tag);
        if (log_.isMatch(LOG_NORMAL)) {
            interfaceLog( std::format("{} transferSize:0x{:0x}", val_.prt(isDebugLog), buffer_size) , tag);
        }
    }
    if (m_writer_waiting) {
        // the next write is already waiting so we need to notify it
        m_channel_sync_event.notify(SC_ZERO_TIME);
        wait(SC_ZERO_TIME);
    }
}

template <class T>
inline T rdy_vld_channel<T>::read()
{
    T tmp;
    read( tmp );
    return tmp;
}

// blocking write

template <class T>
inline void rdy_vld_channel<T>::write( const T& val_ )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    if (isLocking()) { synchLock_->lock(val_.getStructValue()); }
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface, did you set multiwrite?");
    writeCore(val_);
    if (isLocking()) { synchLock_->unlock(); }
}

template <class T>
inline void rdy_vld_channel<T>::writeCore( const T& val_ )
{
     // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    m_multi_writer = true;
    interfaceBase::delay(m_value_written == true);
    m_value_written = true;
    m_value = val_;
    m_valid = true;
    sc_prim_channel::request_update();
    sc_core::wait(m_channel_sync_event);
    m_multi_writer = false;
}

// blocking write with buffer size. This function should be used only for pingpong buffer case with variable size
//  Transactional
template <class T>
inline void rdy_vld_channel<T>::write( const T& val_ , int context)
{
    if (isLocking()) { synchLock_->lock(val_.getStructValue()); }
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface, did you set multiwrite?");
    m_multicycle->setSourceTransactional();   // TODO A2C-154
    while ( m_value_written == true) {
        m_writer_waiting = true;
        sc_core::wait(m_channel_sync_event);
        m_writer_waiting = false;
    }
    m_multicycle->set_write_context(context); // note we have to delay calling this api until after m_value_written is cleared
                                              // context could be tag or length depending on use case
    m_write_context = context; // save the context from the write so that read can use
    writeCore(val_); // go ahead and handle the rest of the write
    if (isLocking()) { synchLock_->unlock(); }
}

// return getReadPtr based on current read buffer index
template <class T>
inline uint8_t * rdy_vld_channel<T>::getReadPtr()
{
    Q_ASSERT(tracker_==nullptr, "getReadPtr not supported with tracker");
    return m_multicycle->getReadPtr(0);
}

// return getWritePtr based on current write buffer index
template <class T>
inline uint8_t * rdy_vld_channel<T>::getWritePtr()
{
    Q_ASSERT(tracker_==nullptr, "getWritePtr not supported with tracker");
    return m_multicycle->getWritePtr(0);
}

// non-transactional write
// note usage of clocked vs transactional interface shall not be mixed
template <class T>
void rdy_vld_channel<T>::writeClocked( const T& val_ )
{
    // if this is not a multicycle interface then just write the value
    if (m_multicycle == nullptr) {
        write(val_);
        return;
    }
    uint32_t tag = val_.getStructValue();
    // detect if we need to perform a transaction
    if (m_multicycle->isNewWriteTransaction()) {
        m_multicycle->initWrite(tag); // initialise the multicycle write
        tag = m_multicycle->get_write_context(); // get the context as it might be coming from list etc
        m_write_context = tag; // save the context from the write so that read can use
        m_write_value = val_; // preserve the header for duration of the transaction
    }
    wait(SC_ZERO_TIME); // ensure one read burst per 'clock' - maybe modify later to set time outside..
    m_multicycle->copyWriteData(tag, (uint8_t *)&val_); // copy the data

    // move to next cycle. Returns true if its on a transaction boarder
    if (m_multicycle->nextWriteCycle()) {
        write(m_write_value); // perform the transaction
    }
}
// note usage of clocked vs transactional interface shall not be mixed
template <class T>
void rdy_vld_channel<T>::readClocked( T& val_)
{
    // if this is not a multicycle interface then just write the value
    if (m_multicycle == nullptr) {
        return read(val_);
    }

    int64_t tag;
    // detect if we need to perform a transaction
    if (m_multicycle->isNewReadTransaction()) {
        read(m_read_value); // perform transaction
        m_value_written = true; //override the transactional read setting of value being valid to ensure writer waits
        if (m_get_struct_value) {
            tag = m_read_value.getStructValue();
        } else {
            tag = m_read_context;
        }
        m_multicycle->initRead(tag); // initialise the multicycle read
    } else {
        if (m_get_struct_value) {
            tag = m_read_value.getStructValue();
        } else {
            tag = m_read_context;
        }
    }
    wait(SC_ZERO_TIME); // ensure one read burst per 'clock' - maybe modify later to set time outside..
    val_ = m_read_value; // ensure header always correct
    m_multicycle->copyReadData(tag, (uint8_t *)&val_);
    // move to next cycle. Returns true if its a new burst
    if (m_multicycle->nextReadCycle()) {
        // new burst
        m_value_written = false; // ensure the write can now continue to next transaction
        if (m_writer_waiting) {
            m_channel_sync_event.notify(SC_ZERO_TIME); // notify the write that the read is complete
            wait(SC_ZERO_TIME);
        }
    }
}

template <class T>
void rdy_vld_channel<T>::status(void)
{
    if (m_ready && m_writer_waiting) {
        log_.logPrint(std::format("{} has deadlock bug", name()), LOG_IMPORTANT);
    }
    int available = num_available();
    if (available > 0) {
        log_.logPrint(std::format("{} has data", name()  ), LOG_IMPORTANT );
        dump();
    }
    teeStatus();
}

template <class T>
inline void rdy_vld_channel<T>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class T>
inline void rdy_vld_channel<T>::print( ::std::ostream& os ) const
{
    os << m_value.prt(isDebugLog) << '\n';
}

template <class T>
inline void rdy_vld_channel<T>::dump( ::std::ostream& os ) const
{
    if (m_value_written) {
        os << m_value.prt(isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}
template <>
inline void rdy_vld_channel<bool>::dump( ::std::ostream& os ) const
{
    if (m_value_written) {
        os << m_value << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class T>
inline ::std::ostream& operator << ( ::std::ostream& os, const rdy_vld_channel<T>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class T>
using rdy_vld_out = sc_port<rdy_vld_out_if< T > >;
template <class T>
using rdy_vld_in = sc_port<rdy_vld_in_if< T > >;

#endif // RDY_VLD_CHANNEL_H
