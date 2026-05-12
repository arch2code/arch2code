// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PUSH_ACK_PORT_THUNKER_H
#define PUSH_ACK_PORT_THUNKER_H

#include "push_ack_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <cstdint>
#include <string>

// push_ack_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream push_ack consumer-side endpoint carrying UpT
// to a downstream push_ack consumer port carrying DownT, when the two
// types are per-field _bitWidth equivalent but differ in nested _packedSt
// width. The per-field equivalence is validated separately in Step 6.2;
// this class performs the runtime packed-value bridge via static_cast and
// preserves the push_ack request / acknowledge handshake at both ends.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (push_ack_in<UpT>&). The port's bound interface is not available
//     until SystemC elaboration completes, so it is resolved lazily on
//     the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its push_ack_in_if<UpT> interface base. The
//     channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpT, class DownT>
class push_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    push_ack_port_thunker( const char* name_,
                           push_ack_in<UpT>&   upPort,
                           push_ack_in<DownT>& downPort,
                           std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    push_ack_port_thunker( const char* name_,
                           sc_core::push_ack_in_if<UpT>& upIface,
                           push_ack_in<DownT>&           downPort,
                           std::string blockName )
      : m_up_port( nullptr ),
        m_up_iface( &upIface ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

private:
    void thunk()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        sc_core::push_ack_in_if<UpT>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            typename UpT::_packedSt inPacked;
            up->pushReceive( inVal );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`); stage the
            // packed value into a local before the cross-width cast.
            inVal.pack( inPacked );
            outVal.unpack( static_cast<typename DownT::_packedSt>( inPacked ) );
            // push() drives the downstream handshake; the concrete
            // push_ack_channel<T>::push override has no default argument,
            // so the magic value is passed explicitly here.
            m_chDown.push( outVal, (uint64_t)-1 );
            up->ack();
        }
    }

    push_ack_in<UpT>*             m_up_port;
    sc_core::push_ack_in_if<UpT>* m_up_iface;
    sc_core::push_ack_channel<DownT> m_chDown;
};

#endif // PUSH_ACK_PORT_THUNKER_H
