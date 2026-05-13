// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_READ_PORT_THUNKER_H
#define AXI_READ_PORT_THUNKER_H

#include "axi_read_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_read_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_read consumer-side endpoint carrying
// (axiReadAddressSt<UpA>, axiReadRespSt<UpD>) to a downstream axi_read
// consumer port carrying (axiReadAddressSt<DownA>, axiReadRespSt<DownD>),
// when the two pairs are per-field _bitWidth equivalent but differ in
// nested _packedSt width. The per-field equivalence is validated
// separately in Step 6.2; this class performs the runtime packed-value
// bridge via copy_packed_bits() in both directions and preserves the AXI
// read handshake at both ends.
//
// Single-beat semantics only: the forwarding loop pulls one address and
// returns one response per iteration. Multi-beat burst transfers are out
// of scope for the thunker; the Stage 6.2 packed-form check is the
// canonical guard against width disagreement for the wrapped envelope.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (axi_read_in<UpA, UpD>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its axi_read_in_if<UpA, UpD> interface base.
//     The channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class DownA, class DownD>
class axi_read_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_read_port_thunker( const char* name_,
                           axi_read_in<UpA, UpD>&     upPort,
                           axi_read_in<DownA, DownD>& downPort,
                           std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    axi_read_port_thunker( const char* name_,
                           axi_read_in_if<UpA, UpD>&  upIface,
                           axi_read_in<DownA, DownD>& downPort,
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
        axi_read_in_if<UpA, UpD>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiReadAddressSt<UpA>   addrIn;
            axiReadAddressSt<DownA> addrOut;
            typename axiReadAddressSt<UpA>::_packedSt addrPacked;
            typename axiReadAddressSt<DownA>::_packedSt addrOutPacked;
            up->receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiReadAddressSt<DownA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_chDown.sendAddr( addrOut, std::nullopt );

            // Data phase: downstream returns, upstream answered.
            axiReadRespSt<DownD> dataIn;
            axiReadRespSt<UpD>   dataOut;
            typename axiReadRespSt<DownD>::_packedSt dataPacked;
            typename axiReadRespSt<UpD>::_packedSt   dataOutPacked;
            m_chDown.receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiReadRespSt<UpD>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            up->sendData( dataOut );
        }
    }

    axi_read_in<UpA, UpD>*    m_up_port;
    axi_read_in_if<UpA, UpD>* m_up_iface;
    axi_read_channel<DownA, DownD> m_chDown;
};

#endif // AXI_READ_PORT_THUNKER_H
