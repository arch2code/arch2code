// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef RDY_VLD_PORT_THUNKER_H
#define RDY_VLD_PORT_THUNKER_H

#include "rdy_vld_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// rdy_vld_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream rdy_vld consumer-side endpoint carrying UpT to
// a downstream rdy_vld consumer port carrying DownT, when the two types are
// per-field _bitWidth equivalent but differ in nested _packedSt width. The
// per-field equivalence is validated separately in Step 6.2; this class
// performs the runtime packed-value bridge via static_cast.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (rdy_vld_in<UpT>&). The port's bound interface is not available
//     until SystemC elaboration completes, so it is resolved lazily on
//     the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its rdy_vld_in_if<UpT> interface base. The
//     channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpT, class DownT>
class rdy_vld_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    rdy_vld_port_thunker( const char* name_,
                          rdy_vld_in<UpT>&   upPort,
                          rdy_vld_in<DownT>& downPort,
                          std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    rdy_vld_port_thunker( const char* name_,
                          sc_core::rdy_vld_in_if<UpT>& upIface,
                          rdy_vld_in<DownT>&           downPort,
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
        sc_core::rdy_vld_in_if<UpT>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            up->readClocked( inVal );
            outVal.unpack( static_cast<typename DownT::_packedSt>( inVal.pack() ) );
            m_chDown.writeClocked( outVal );
        }
    }

    rdy_vld_in<UpT>*             m_up_port;
    sc_core::rdy_vld_in_if<UpT>* m_up_iface;
    sc_core::rdy_vld_channel<DownT> m_chDown;
};

#endif // RDY_VLD_PORT_THUNKER_H
