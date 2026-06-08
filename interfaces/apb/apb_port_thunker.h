// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef APB_PORT_THUNKER_H
#define APB_PORT_THUNKER_H

#include "apb_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// apb_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream APB consumer-side endpoint carrying (UpA,
// UpD) to a downstream APB consumer port carrying (DownA, DownD), when
// the two pairs are per-field _bitWidth equivalent but differ in nested
// _packedSt width. Per-field equivalence is validated elsewhere; this
// class performs the runtime packed-value bridge via copy_packed_bits()
// in both directions and preserves the APB request / completion handshake
// at both ends.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// APB handshake notes (see apb_channel.h):
//   * The completer side accepts a transaction via
//     reqReceive(isWrite, addrIn, dataIn). For write transactions the
//     channel already acknowledges by clearing the pending request, so
//     no complete() call is issued by the thunker for writes. For read
//     transactions the thunker pack-converts the response data and
//     calls complete() with the converted data.
//   * The requester side issues a single round trip per transaction via
//     request(isWrite, addrOut, dataInOut). The function blocks until the
//     response is in dataInOut for reads, and returns after acknowledging
//     the write for writes.
//
// Three construction shapes are supported. The first two are
// consumer-side (the downstream child end is an APB consumer,
// apb_in<DownA, DownD>&); the third is producer-side (the downstream
// child end is an APB producer, apb_out<DownA, DownD>&):
//   * connectionMap shape — the up side is a parent port
//     (apb_in<UpA, UpD>&). The port's bound interface is not available
//     until SystemC elaboration completes, so it is resolved lazily on
//     the first iteration of thunkIn().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its apb_in_if<UpA, UpD> interface base. The
//     channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//   * producer (out) shape — the downstream child end is a producer
//     port (apb_out<DownA, DownD>&) that drives the owned channel; the
//     thunker receives from the owned channel and issues the bridged
//     request onto the parent-side channel's apb_out_if<UpA, UpD>.
//     Data flows child -> parent here, the reverse of the consumer
//     shapes. Used when a parameterized producer instance feeds a
//     non-parameterized container channel.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (apb_in vs apb_out), so the container generator emits
// identical wiring for both directions.
template <class UpA, class UpD, class DownA, class DownD>
class apb_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    apb_port_thunker( const char* name_,
                      apb_in<UpA, UpD>&     upPort,
                      apb_in<DownA, DownD>& downPort,
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
    apb_port_thunker( const char* name_,
                      sc_core::apb_in_if<UpA, UpD>& upInIface,
                      apb_in<DownA, DownD>&         downPort,
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
    // that drives the owned channel; the bridged request is issued onto
    // the parent-side channel's apb_out_if<UpA, UpD>.
    apb_port_thunker( const char* name_,
                      sc_core::apb_out_if<UpA, UpD>& upOutIface,
                      apb_out<DownA, DownD>&         downPort,
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
        sc_core::apb_in_if<UpA, UpD>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            bool   isWrite = false;
            UpA    addrIn;
            UpD    dataIn;
            DownA  addrOut;
            DownD  dataOut;
            typename UpA::_packedSt addrPacked;
            typename DownA::_packedSt addrOutPacked;
            typename UpD::_packedSt dataPacked;
            typename DownD::_packedSt dataOutPacked;
            upIn->reqReceive( isWrite, addrIn, dataIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, DownA::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // For reads dataIn is unused; for writes it carries the
            // upstream write payload. Convert it unconditionally — the
            // downstream request() ignores the data on reads, and on
            // writes the converted value is what must reach the
            // downstream completer.
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, DownD::_bitWidth );
            dataOut.unpack( dataOutPacked );
            // request() blocks until the read response arrives, or until
            // the write ack is observed for writes.
            m_down_channel.request( isWrite, addrOut, dataOut );
            if (!isWrite) {
                // Convert the downstream read response back to up-side
                // typing and complete the transaction. Writes are
                // already acknowledged by apb_channel::reqReceive() —
                // calling complete() on a write would trip its assertion.
                UpD dataUp;
                typename DownD::_packedSt respPacked;
                typename UpD::_packedSt   respUpPacked;
                dataOut.pack( respPacked );
                copy_packed_bits( respUpPacked, respPacked, UpD::_bitWidth );
                dataUp.unpack( respUpPacked );
                upIn->complete( dataUp );
            }
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD
        // into the owned m_down_channel; bridge each transaction and
        // issue the request onto the parent-side channel. This is
        // thunkIn() with the consumer and producer objects swapped and
        // every Up<->Down type swapped, preserving the same APB handshake
        // asymmetry (complete() only on reads).
        while (true) {
            bool   isWrite = false;
            DownA  addrIn;
            DownD  dataIn;
            UpA    addrOut;
            UpD    dataOut;
            typename DownA::_packedSt addrPacked;
            typename UpA::_packedSt   addrOutPacked;
            typename DownD::_packedSt dataPacked;
            typename UpD::_packedSt   dataOutPacked;
            m_down_channel.reqReceive( isWrite, addrIn, dataIn );
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, UpA::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // For reads dataIn is unused; for writes it carries the
            // child-side write payload. Convert it unconditionally — the
            // up-side request() ignores the data on reads, and on writes
            // the converted value is what must reach the up-side completer.
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, UpD::_bitWidth );
            dataOut.unpack( dataOutPacked );
            // request() blocks until the read response arrives, or until
            // the write ack is observed for writes.
            m_up_out_iface->request( isWrite, addrOut, dataOut );
            if (!isWrite) {
                // Convert the up-side read response back to down-side
                // typing and complete the transaction. Writes are
                // already acknowledged by apb_channel::reqReceive() —
                // calling complete() on a write would trip its assertion.
                DownD respDown;
                typename UpD::_packedSt   respPacked;
                typename DownD::_packedSt respDownPacked;
                dataOut.pack( respPacked );
                copy_packed_bits( respDownPacked, respPacked, DownD::_bitWidth );
                respDown.unpack( respDownPacked );
                m_down_channel.complete( respDown );
            }
        }
    }

    apb_in<UpA, UpD>*              m_up_port;
    sc_core::apb_in_if<UpA, UpD>*  m_up_in_iface;
    sc_core::apb_out_if<UpA, UpD>* m_up_out_iface;
    sc_core::apb_channel<DownA, DownD> m_down_channel;
};

#endif // APB_PORT_THUNKER_H
