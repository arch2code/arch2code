// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PUSH_ACK_PORT_THUNKER_H
#define PUSH_ACK_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
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
// width. Per-field equivalence is validated elsewhere; this class performs
// the runtime packed-value bridge via copy_packed_bits() and preserves the
// push_ack request / acknowledge handshake at both ends.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Three construction shapes are supported. The first two are
// consumer-side (the downstream child end is a push_ack consumer,
// push_ack_in<DownT>&); the third is producer-side (the downstream
// child end is a push_ack producer, push_ack_out<DownT>&):
//   * connectionMap shape — the up side is a parent port
//     (push_ack_in<UpT>&). The port's bound interface is not available
//     until SystemC elaboration completes, so it is resolved lazily on
//     the first iteration of thunkIn().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its push_ack_in_if<UpT> interface base. The
//     channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//   * producer (out) shape — the downstream child end is a producer
//     port (push_ack_out<DownT>&) that pushes into the owned channel;
//     the thunker consumes from the owned channel and pushes the
//     bridged payload onto the parent-side channel's push_ack_out_if<UpT>.
//     Data flows child -> parent here, the reverse of the consumer
//     shapes. Used when a parameterized producer instance feeds a
//     non-parameterized container channel.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (push_ack_in vs push_ack_out), so the container
// generator emits identical wiring for both directions.
template <class UpT, class DownT>
class push_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    push_ack_port_thunker( const char* name_,
                           push_ack_in<UpT>&   upPort,
                           push_ack_in<DownT>& downPort,
                           std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    push_ack_port_thunker( const char* name_,
                           sc_core::push_ack_in_if<UpT>& upInIface,
                           push_ack_in<DownT>&           downPort,
                           std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // producer (out) shape: the downstream child end is a producer port
    // that pushes into the owned channel; the bridged payload is pushed
    // onto the parent-side channel's push_ack_out_if<UpT>.
    push_ack_port_thunker( const char* name_,
                           sc_core::push_ack_out_if<UpT>& upOutIface,
                           push_ack_out<DownT>&           downPort,
                           std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

private:
    void thunkIn()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        sc_core::push_ack_in_if<UpT>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            typename UpT::_packedSt inPacked;
            typename DownT::_packedSt outPacked;
            upIn->pushReceive( inVal );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            inVal.pack( inPacked );
            copy_packed_bits( outPacked, inPacked, DownT::_bitWidth );
            outVal.unpack( outPacked );
            // push() drives the downstream handshake; the concrete
            // push_ack_channel<T>::push override has no default argument,
            // so the magic value is passed explicitly here.
            m_down_channel.push( outVal, (uint64_t)-1 );
            upIn->ack();
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer pushes DownT into the
        // owned m_down_channel; bridge each payload and push UpT onto the
        // parent-side channel. Acking the child only after the parent push
        // completes preserves end-to-end backpressure, mirroring thunkIn().
        while (true) {
            DownT inVal;
            UpT   outVal;
            typename DownT::_packedSt inPacked;
            typename UpT::_packedSt   outPacked;
            m_down_channel.pushReceive( inVal );
            inVal.pack( inPacked );
            copy_packed_bits( outPacked, inPacked, UpT::_bitWidth );
            outVal.unpack( outPacked );
            m_up_out_iface->push( outVal, (uint64_t)-1 );
            m_down_channel.ack();
        }
    }

    push_ack_in<UpT>*                m_up_port;
    sc_core::push_ack_in_if<UpT>*    m_up_in_iface;
    sc_core::push_ack_out_if<UpT>*   m_up_out_iface;
    sc_core::push_ack_channel<DownT> m_down_channel;
};

#endif // PUSH_ACK_PORT_THUNKER_H
