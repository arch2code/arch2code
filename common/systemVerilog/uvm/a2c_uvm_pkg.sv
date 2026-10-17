`ifndef A2C_UVM_PKG_SV
`define A2C_UVM_PKG_SV

`timescale 1ns/1ps

// What the interface agent packages share.
package a2c_uvm_pkg;

    // The side of the interface an agent plays, the opposite of the DUT
    // port's modport: a DUT dst input gets an A2C_SRC agent.
    typedef enum {A2C_SRC, A2C_DST} a2c_role_e;

    // The A2C_TXN line every monitor logs per transaction: the time in ns,
    // the port, the role, the item's fields, and the packed value in hex so a
    // SystemC test can rebuild the payload with sc_unpack().
    function automatic string a2c_txn(string path, a2c_role_e role, string fields, string hex);
        return $sformatf("A2C_TXN %0.3f %s %s %s hex=%s", $realtime, path,
                         (role == A2C_SRC) ? "src" : "dst", fields, hex);
    endfunction

endpackage : a2c_uvm_pkg

`endif // A2C_UVM_PKG_SV
