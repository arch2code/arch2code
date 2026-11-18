//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafA
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: leafA
module leafA
// Generated Import package statement(s)
import ahbDecode_package::*;
(
    ahb_if.dst ahbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(cfgRegSt)) cfgA();
    status_if #(.data_t(statRegSt)) statA();
    external_reg_if #(.data_t(cmdRegSt)) cmdA();

    // Memory Interfaces
    memory_if #(.data_t(tblSt), .addr_t(tblAddrSt)) tblA_reg();

// Instances
leafARegs uleafARegs (
    .ahbReg (ahbReg),
    .tblA (tblA_reg),
    .cfgA (cfgA),
    .statA (statA),
    .cmdA (cmdA),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
memory_sp #(.DEPTH(TBL_WORDS), .data_t(tblSt)) uTblA (
    .mem_port (tblA_reg),
    .clk (clk)
);

// GENERATED_CODE_END

    assign statA.data.value = 16'h5a5a;

    // cmdA's owner refuses a write of 0x0bad and keeps the value it holds.
    logic cmdRefused;
    assign cmdRefused = cmdA.wdata.value == 16'h0bad;
    assign cmdA.pslverr = cmdRefused;
    localparam cmdRegSt CMD_RESET = '{value: 16'h0c0d};
    `DFFR_INST(cmdRegSt, cmdReg, CMD_RESET)
    always_comb begin
        n_cmdReg = cmdReg;
        if (|cmdA.write && !cmdRefused) begin
            n_cmdReg = cmdA.wdata;
        end
    end
    assign cmdA.rdata = cmdReg;

endmodule: leafA
