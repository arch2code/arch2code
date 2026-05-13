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
// _packedSt width. The per-field equivalence is validated separately in
// Step 6.2; this class performs the runtime packed-value bridge via
// copy_packed_bits() in both directions and preserves the APB request /
// completion handshake at both ends.
//
// APB handshake notes (see apb_channel.h):
//   * The completer (up) side accepts a transaction via
//     reqReceive(isWrite, addrIn, dataIn). For write transactions the
//     channel already acknowledges by clearing the pending request, so
//     no complete() call is issued by the thunker for writes. For read
//     transactions the thunker pack-converts the response data and
//     calls up->complete() with the converted up-side data.
//   * The requester (down) side issues a single round trip per
//     transaction via request(isWrite, addrOut, dataInOut). The function
//     blocks until the response is in dataInOut for reads, and returns
//     after acknowledging the write for writes.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (apb_in<UpA, UpD>&). The port's bound interface is not available
//     until SystemC elaboration completes, so it is resolved lazily on
//     the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its apb_in_if<UpA, UpD> interface base. The
//     channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class DownA, class DownD>
class apb_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    apb_port_thunker( const char* name_,
                      apb_in<UpA, UpD>&     upPort,
                      apb_in<DownA, DownD>& downPort,
                      std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    apb_port_thunker( const char* name_,
                      sc_core::apb_in_if<UpA, UpD>& upIface,
                      apb_in<DownA, DownD>&         downPort,
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
        sc_core::apb_in_if<UpA, UpD>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
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
            up->reqReceive( isWrite, addrIn, dataIn );
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
            m_chDown.request( isWrite, addrOut, dataOut );
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
                up->complete( dataUp );
            }
        }
    }

    apb_in<UpA, UpD>*             m_up_port;
    sc_core::apb_in_if<UpA, UpD>* m_up_iface;
    sc_core::apb_channel<DownA, DownD> m_chDown;
};

#endif // APB_PORT_THUNKER_H
