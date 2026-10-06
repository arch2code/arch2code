// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_READ_PORT_THUNKER_H
#define AXI_READ_PORT_THUNKER_H

#include "axi_read_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include <memory>
#include <optional>
#include <queue>
#include <string>
#include <type_traits>
#include <vector>

// axi_read_port_thunker
//
// Joins a child axi_read port to the parent's endpoint when the payload types
// are per-field _bitWidth equivalent but distinct C++ types. Up is the parent
// side and Down the child, whatever the data direction.
//
// It owns no channel and no thread. The adapter converts every child call,
// portBase calls such as setCycleTransaction included, and makes it on the
// parent's channel, so timing and API mode are those of a direct bind.
//
// Where a verdict is false, copyPayload's packed arm masks each field to its
// declared width. A value with bits outside its range is then cleaned up here
// instead of failing fast as it would on a direct bind. This is an accepted
// limitation.
//
// getWritePtr()/getReadPtr() hand the child raw memory in the parent's burst
// buffer, which the thunker never sees. Unless kDirectData holds, the two sides
// lay out a beat differently, so the adapter gives the child a Down-typed copy
// of 256 beats (the AXI maximum) and converts it on buffered sendData() and
// getReadPtr(). Receive lengths come from the arlen forwarded for that rid.
//
// A parent port is unbound until elaboration completes, so it is resolved in
// end_of_elaboration(). Template argument order must match _thunker_member_type
// in pysrc/intf_gen_utils.py. block_ is unused.
template <class UpA, class UpD, class DownA, class DownD,
          bool DirectAddr = false, bool DirectData = false,
          class UpARU = std::monostate, class UpRU = std::monostate, class UpID = _axiIdT, unsigned UpIDW = 4,
          class DownARU = std::monostate, class DownRU = std::monostate, class DownID = _axiIdT, unsigned DownIDW = 4>
class axi_read_port_thunker
{
    static_assert(UpIDW == DownIDW, "a cross-interface bind must carry the same id_t width on both ends");
    static_assert(!DirectAddr || sizeof(UpA) == sizeof(DownA), "direct copy requires equal payload size");
    static_assert(!DirectData || sizeof(UpD) == sizeof(DownD), "direct copy requires equal payload size");

    using UpAddr = axiReadAddressSt<UpA, UpARU, UpID, UpIDW>;
    using DownAddr = axiReadAddressSt<DownA, DownARU, DownID, DownIDW>;
    using UpResp = axiReadRespSt<UpD, UpRU, UpID, UpIDW>;
    using DownResp = axiReadRespSt<DownD, DownRU, DownID, DownIDW>;
    using UpIn = axi_read_in_if<UpA, UpD, UpARU, UpRU, UpID, UpIDW>;
    using UpOut = axi_read_out_if<UpA, UpD, UpARU, UpRU, UpID, UpIDW>;
    using DownIn = axi_read_in_if<DownA, DownD, DownARU, DownRU, DownID, DownIDW>;
    using DownOut = axi_read_out_if<DownA, DownD, DownARU, DownRU, DownID, DownIDW>;

    static constexpr bool kDirectData = DirectData && std::is_same_v<UpRU, DownRU> && std::is_same_v<UpID, DownID>;
    static_assert(!kDirectData || sizeof(UpResp) == sizeof(DownResp), "a shared burst buffer requires equal envelope size");
    static constexpr unsigned kMaxBurst = 1u << UpAddr::lenWidth;

public:
    // connectionMap shape: parent port reference.
    axi_read_port_thunker( const char* name_,
                           axi_read_in<UpA, UpD, UpARU, UpRU, UpID, UpIDW>&     upPort,
                           axi_read_in<DownA, DownD, DownARU, DownRU, DownID, DownIDW>& downPort,
                           std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upPort );
        downPort( *m_in );
    }

    // connections shape: parent-side channel bound by its interface base.
    axi_read_port_thunker( const char* name_,
                           axi_read_in_if<UpA, UpD, UpARU, UpRU, UpID, UpIDW>&  upInIface,
                           axi_read_in<DownA, DownD, DownARU, DownRU, DownID, DownIDW>& downPort,
                           std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upInIface );
        downPort( *m_in );
    }

    // producer (out) shape: the child producer port drives the parent-side
    // channel's axi_read_out_if<UpA, UpD>.
    axi_read_port_thunker( const char* name_,
                           axi_read_out_if<UpA, UpD, UpARU, UpRU, UpID, UpIDW>&  upOutIface,
                           axi_read_out<DownA, DownD, DownARU, DownRU, DownID, DownIDW>& downPort,
                           std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upOutIface );
        downPort( *m_out );
    }

    // producer (out) port shape: the parent side is a parent OUT port.
    axi_read_port_thunker( const char* name_,
                           axi_read_out<UpA, UpD, UpARU, UpRU, UpID, UpIDW>&     upPort,
                           axi_read_out<DownA, DownD, DownARU, DownRU, DownID, DownIDW>& downPort,
                           std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upPort );
        downPort( *m_out );
    }

private:
    template <class To, class From>
    static void copyAddr( To& out, const From& in )
    {
        out.arid = static_cast<decltype(out.arid)>( in.arid );
        copyPayload<DirectAddr>( out.araddr, in.araddr );
        out.arlen = in.arlen;
        out.arsize = in.arsize;
        out.arburst = in.arburst;
        if constexpr (hasOptionalPayload<decltype(out.user)> && hasOptionalPayload<decltype(in.user)>) {
            copyPayload<false>( out.user, in.user );
        }
    }

    template <class To, class From>
    static void copyResp( To& out, const From& in )
    {
        out.rid = static_cast<decltype(out.rid)>( in.rid );
        copyPayload<DirectData>( out.rdata, in.rdata );
        out.rresp = in.rresp;
        out.rlast = in.rlast;
        if constexpr (hasOptionalPayload<decltype(out.user)> && hasOptionalPayload<decltype(in.user)>) {
            copyPayload<false>( out.user, in.user );
        }
    }

    // The portBase calls the child makes through its port, forwarded to the
    // parent's interface as a direct bind would deliver them.
    template <class UpIf>
    struct forwardPortBase : virtual public portBase
    {
        void setMultiDriver( std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr ) override { m_up->setMultiDriver( name_, prt ); }
        std::shared_ptr<trackerBase> getTracker( void ) override { return m_up->getTracker(); }
        void setTeeBusy( bool busy ) override { m_up->setTeeBusy( busy ); }
        void setTandem( void ) override { m_up->setTandem(); }
        void setLogging( verbosity_e verbosity ) override { m_up->setLogging( verbosity ); }
        void setTimed( int nsec, timedDelayMode mode ) override { m_up->setTimed( nsec, mode ); }
        void setCycleTransaction( portType type_ ) override { m_up->setCycleTransaction( type_ ); }
        void setTimedDelayPtr( std::shared_ptr<timedDelayBase> pTimedDelay ) override { m_up->setTimedDelayPtr( pTimedDelay ); }
        portBase* getPort( void ) override { return m_up->getPort(); }
        sc_core::sc_prim_channel* getChannel( void ) override { return m_up->getChannel(); }
        void setLogQueue( std::shared_ptr<stringPingPong> logQueue ) override { m_up->setLogQueue( logQueue ); }

        UpIf* m_up = nullptr;
        sc_core::sc_port<UpIf>* m_up_port = nullptr;
    };

    // Consumer child: the child receives AR and sends R.
    class inAdapter final : public sc_core::sc_prim_channel, public DownIn, public forwardPortBase<UpIn>
    {
    public:
        inAdapter( const char* name_, sc_core::sc_port<UpIn>& upPort ) : sc_core::sc_prim_channel( name_ ) { this->m_up_port = &upPort; }
        inAdapter( const char* name_, UpIn& up ) : sc_core::sc_prim_channel( name_ ) { this->m_up = &up; }

        void receiveAddr( DownAddr& addr_ ) override
        {
            UpAddr up;
            this->m_up->receiveAddr( up );
            copyAddr( addr_, up );
        }
        void sendData( const DownResp& data_ ) override
        {
            if constexpr (!kDirectData) {
                const unsigned beats = getSendBufferCapacity();
                if (beats) {
                    Q_ASSERT( beats <= kMaxBurst, "read response buffer exceeds maximum AXI burst" );
                    UpResp* up = reinterpret_cast<UpResp*>( this->m_up->getWritePtr() );
                    for (unsigned i = 0; i < beats; i++) {
                        copyResp( up[i], m_shadow[i] );
                    }
                }
            }
            UpResp up;
            copyResp( up, data_ );
            this->m_up->sendData( up );
        }
        void sendData( const DownResp& data_, int burst_count ) override
        {
            if constexpr (!kDirectData) {
                UpResp* up = reinterpret_cast<UpResp*>( this->m_up->getWritePtr() );
                for (int i = 0; i < burst_count; i++) {
                    copyResp( up[i], m_shadow[i] );
                }
            }
            UpResp up;
            copyResp( up, data_ );
            this->m_up->sendData( up, burst_count );
        }
        void sendDataCycle( const DownResp& data_ ) override
        {
            UpResp up;
            copyResp( up, data_ );
            this->m_up->sendDataCycle( up );
        }
        uint8_t* getWritePtr( void ) override
        {
            if constexpr (kDirectData) {
                return this->m_up->getWritePtr();
            } else {
                return reinterpret_cast<uint8_t*>( m_shadow.data() );
            }
        }
        bool isActive() override { return this->m_up->isActive(); }
        uint32_t getSendBufferCapacity(void) override { return this->m_up->getSendBufferCapacity(); }
        bool isNotActive() override { return this->m_up->isNotActive(); }
        void setExternalEvent( sc_event* event ) override { this->m_up->setExternalEvent( event ); }
        const char* kind() const override { return "axi_read_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
        std::vector<DownResp> m_shadow = std::vector<DownResp>( kDirectData ? 0 : kMaxBurst );
    };

    // Producer child: the child sends AR and receives R.
    class outAdapter final : public sc_core::sc_prim_channel, public DownOut, public forwardPortBase<UpOut>
    {
    public:
        outAdapter( const char* name_, sc_core::sc_port<UpOut>& upPort ) : sc_core::sc_prim_channel( name_ ) { this->m_up_port = &upPort; }
        outAdapter( const char* name_, UpOut& up ) : sc_core::sc_prim_channel( name_ ) { this->m_up = &up; }

        void sendAddr( const DownAddr& addr_, std::optional<std::string> str ) override
        {
            // Burst lengths per id, for the buffer conversion in getReadPtr().
            // A cycle-mode child reads no buffer, so records nothing.
            if constexpr (!kDirectData) {
                if (!m_cycle) {
                    m_beats[addr_.arid].push( addr_.arlen + 1u );
                }
            }
            UpAddr up;
            copyAddr( up, addr_ );
            this->m_up->sendAddr( up, std::move( str ) );
        }
        void receiveData( DownResp& data_ ) override
        {
            UpResp up;
            this->m_up->receiveData( up );
            copyResp( data_, up );
            // A transactional receive delivers one whole burst.
            if constexpr (!kDirectData) {
                std::queue<unsigned>& beats = m_beats[up.rid];
                m_received = beats.front();
                beats.pop();
            }
        }
        void receiveDataCycle( DownResp& data_ ) override
        {
            UpResp up;
            this->m_up->receiveDataCycle( up );
            copyResp( data_, up );
        }
        // Only a channel with a burst buffer has a read pointer, so the burst is
        // converted here rather than on every receiveData().
        uint8_t* getReadPtr( void ) override
        {
            if constexpr (kDirectData) {
                return this->m_up->getReadPtr();
            } else {
                const UpResp* up = reinterpret_cast<const UpResp*>( this->m_up->getReadPtr() );
                for (unsigned i = 0; i < m_received; i++) {
                    copyResp( m_shadow[i], up[i] );
                }
                return reinterpret_cast<uint8_t*>( m_shadow.data() );
            }
        }
        void push_burst( uint32_t burstCount ) override { this->m_up->push_burst( burstCount ); }
        void setCycleTransaction( portType type_ ) override
        {
            m_cycle = true;
            this->m_up->setCycleTransaction( type_ );
        }
        const char* kind() const override { return "axi_read_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
        std::vector<DownResp> m_shadow = std::vector<DownResp>( kDirectData ? 0 : kMaxBurst );
        std::vector<std::queue<unsigned>> m_beats = std::vector<std::queue<unsigned>>( kDirectData ? 0 : 1u << DownIDW );
        unsigned m_received = 0;
        bool m_cycle = false;
    };

    // One of the two, by construction shape.
    std::unique_ptr<inAdapter> m_in;
    std::unique_ptr<outAdapter> m_out;
};

#endif // AXI_READ_PORT_THUNKER_H
