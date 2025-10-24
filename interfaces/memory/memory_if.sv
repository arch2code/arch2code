interface memory_if #(
        parameter type data_t = logic,
        parameter type addr_t = logic
    );

    data_t write_data;
    data_t read_data;
    addr_t addr;
    logic enable;
    logic wr_en; // Write Enable

    // Source
    modport src (output write_data, addr, enable, wr_en,  input read_data);

    // Destination
    modport dst ( input write_data, addr, enable, wr_en, output read_data);

endinterface : memory_if
