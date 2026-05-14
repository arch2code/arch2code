// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_THUNKER_H
#define AXI_WRITE_PORT_THUNKER_H

#include "axi_write_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_write_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_write consumer-side endpoint carrying
// (axiWriteAddressSt<UpA>, axiWriteDataSt<UpD, UpS>) and the upstream
// response axiWriteRespSt to a downstream axi_write consumer port carrying
// (axiWriteAddressSt<DownA>, axiWriteDataSt<DownD, DownS>) and the
// downstream response axiWriteRespSt, when the corresponding payload
// structures are per-field _bitWidth equivalent but differ in nested
// _packedSt width. The per-field equivalence is validated separately in
// Step 6.2; this class performs the runtime packed-value bridge for the
// per-parameter envelope fields via copy_packed_bits() and preserves the
// AXI write address / data / response handshake at both ends.
//
// Single-beat semantics only: the forwarding loop pulls one address, one
// data beat and one response per iteration. Multi-beat burst transfers
// and partial writes are out of scope for the thunker; the Stage 6.2
// packed-form check is the canonical guard against width disagreement
// for the wrapped envelope.
//
// The fourth and fifth payload structs of the axi_write view are the
// strobe types (UpS / DownS). axi_write_if.yaml lists three struct
// parameters per side (addr_t, data_t, strb_t), so the template parameter
// list carries six types — three per side — matching the buildThunkerView
// enumeration order.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (axi_write_in<UpA, UpD, UpS>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its axi_write_in_if<UpA, UpD, UpS> interface
//     base. The channel is fully constructed before the thunker is, so
//     the interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class UpS,
          class DownA, class DownD, class DownS>
class axi_write_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_write_port_thunker( const char* name_,
                            axi_write_in<UpA, UpD, UpS>&     upPort,
                            axi_write_in<DownA, DownD, DownS>& downPort,
                            std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    axi_write_port_thunker( const char* name_,
                            axi_write_in_if<UpA, UpD, UpS>&    upIface,
                            axi_write_in<DownA, DownD, DownS>& downPort,
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
        axi_write_in_if<UpA, UpD, UpS>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiWriteAddressSt<UpA>   addrIn;
            axiWriteAddressSt<DownA> addrOut;
            typename axiWriteAddressSt<UpA>::_packedSt addrPacked;
            typename axiWriteAddressSt<DownA>::_packedSt addrOutPacked;
            up->receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiWriteAddressSt<DownA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_chDown.sendAddr( addrOut, std::nullopt );

            // Data phase: upstream receives, downstream sends.
            axiWriteDataSt<UpD, UpS>     dataIn;
            axiWriteDataSt<DownD, DownS> dataOut;
            typename axiWriteDataSt<UpD, UpS>::_packedSt dataPacked;
            typename axiWriteDataSt<DownD, DownS>::_packedSt dataOutPacked;
            up->receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiWriteDataSt<DownD, DownS>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            m_chDown.sendData( dataOut );

            // Response phase: downstream returns, upstream answered.
            axiWriteRespSt respIn;
            axiWriteRespSt respOut;
            typename axiWriteRespSt::_packedSt respPacked;
            typename axiWriteRespSt::_packedSt respOutPacked;
            m_chDown.receiveResp( respIn );
            respIn.pack( respPacked );
            copy_packed_bits( respOutPacked, respPacked, axiWriteRespSt::_bitWidth );
            respOut.unpack( respOutPacked );
            up->sendResp( respOut );
        }
    }

    axi_write_in<UpA, UpD, UpS>*    m_up_port;
    axi_write_in_if<UpA, UpD, UpS>* m_up_iface;
    axi_write_channel<DownA, DownD, DownS> m_chDown;
};

#endif // AXI_WRITE_PORT_THUNKER_H
