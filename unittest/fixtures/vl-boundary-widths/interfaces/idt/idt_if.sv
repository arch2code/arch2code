// Test protocol: required struct/type/typeStruct plus optional struct/type/typeStruct.
interface idt_if #(
        parameter type s_t  = logic,
        parameter type ty_t = logic,
        parameter type ts_t = logic,
        parameter type o1_t = logic [1:0],
        parameter type o2_t = logic [2:0],
        parameter type o3_t = logic [4:0]
    );
    logic  vld;
    s_t    s;
    ty_t   ty;
    ts_t   ts;
    o1_t   o1;
    o2_t   o2;
    o3_t   o3;
    logic  rdy;
    modport src (output vld, s, ty, ts, o1, o2, o3, input rdy);
    modport dst (input vld, s, ty, ts, o1, o2, o3, output rdy);
endinterface : idt_if
