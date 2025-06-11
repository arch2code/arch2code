INTF_DEFS = {
    'status' : {
        'parameters' : {
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'data' : 'data_t'
        },
        'modports' : {
            'src' : {
                'inputs' : [],
                'outputs': ['data']
            },
            'dst' : {
                'inputs' : ['data'],
                'outputs': []
            }
        },
        'sc_channel' : {
           'type' : 'status',
           'param_cast' : None,
           'multicycle_types' : []
        },
    },
    'rdy_vld' : {
        'parameters' : {
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'vld' : 'bool',
            'data' : 'data_t',
            'rdy' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['rdy'],
                'outputs': ['vld', 'data']
            },
            'dst' : {
                'inputs' : ['vld', 'data'],
                'outputs': ['rdy']
            }
        },
        'sc_channel' : {
            'type' : 'rdy_vld',
            'param_cast' : None,
            'multicycle_types' : ['fixed_size', 'api_list_tracker',  'api_list_size']
        }
    },
    'req_ack' : {
        'parameters' : {
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' },
            'rdata_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'req' : 'bool',
            'data' : 'data_t',
            'ack' : 'bool',
            'rdata' : 'rdata_t'
        },
        'modports' : {
            'src' : {
                'inputs' : ['ack', 'rdata'],
                'outputs': ['req', 'data']
            },
            'dst' : {
                'inputs' : ['req', 'data'],
                'outputs': ['ack', 'rdata']
            }
        },
        'sc_channel' : {
            'type' : 'req_ack',
            'param_cast' : None,
            'multicycle_types' : []
        }
    },
    'push_ack' : {
        'parameters' : {
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'push' : 'bool',
            'data' : 'data_t',
            'ack' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['ack'],
                'outputs': ['push', 'data']
            },
            'dst' : {
                'inputs' : ['push', 'data'],
                'outputs': ['ack']
            }
        },
        'sc_channel' : {
            'type' : 'push_ack',
            'param_cast' : None,
            'multicycle_types' : []
        }
    },
    'pop_ack' : {
        'parameters' : {
            'rdata_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'pop' : 'bool',
            'ack' : 'bool',
            'rdata' : 'rdata_t',
        },
        'modports' : {
            'src' : {
                'inputs' : ['ack', 'rdata'],
                'outputs': ['pop']
            },
            'dst' : {
                'inputs' : ['pop'],
                'outputs': ['ack', 'rdata']
            }
        },
        'sc_channel' : {
            'type' : 'pop_ack',
            'param_cast' : None,
            'multicycle_types' : []
        }
    },
    'apb' : {
        'parameters' : {
            'addr_t' : { 'datatype' : 'struct', 'default' : 'bit' },
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'paddr' : 'addr_t',
            'psel' : 'bool',
            'penable' : 'bool',
            'pwrite' : 'bool',
            'pwdata' : 'data_t',
            'pready' : 'bool',
            'prdata' : 'data_t',
            'pslverr' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['pready', 'prdata', 'pslverr'],
                'outputs': ['paddr', 'psel', 'penable', 'pwrite', 'pwdata']
            },
            'dst' : {
                'inputs' : ['paddr', 'psel', 'penable', 'pwrite', 'pwdata'],
                'outputs': ['pready', 'prdata', 'pslverr']
            }
        },
        'sc_channel' : {
            'type' : 'apb',
            'param_cast' : None,
            'multicycle_types' : []
        }
    },
    'notify_ack' : {
        'parameters' : {
        },
        'signals' : {
            'notify' : 'bool',
            'ack' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['ack'],
                'outputs': ['notify']
            },
            'dst' : {
                'inputs' : ['notify'],
                'outputs': ['ack']
            }
        },
        'sc_channel' : {
            'type' : 'notify_ack',
            'param_cast' : None,
            'multicycle_types' : []
        }
    },
    'axi_read' : {
        'parameters' : {
            'addr_t' : { 'datatype' : 'struct', 'default' : 'bit' },
            'data_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'araddr': 'addr_t',
            'arid' : 'bit [3:0]',
            'arlen' : 'bit [7:0]',
            'arsize' : 'bit [2:0]',
            'arburst' : 'bit [1:0]',
            'arvalid' : 'bool',
            'arready': 'bool',
            'rdata' : 'data_t',
            'rid': 'bit [3:0]',
            'rresp' : 'bit [1:0]',
            'rlast' : 'bool',
            'rvalid': 'bool',
            'rready' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['arready', 'rid', 'rdata', 'rresp', 'rlast', 'rvalid'],
                'outputs': ['arid', 'araddr', 'arlen', 'arsize', 'arburst', 'arvalid', 'rready']
            },
            'dst' : {
                'inputs' : ['arid', 'araddr', 'arlen', 'arsize', 'arburst', 'arvalid', 'rready'],
                'outputs': ['arready', 'rid', 'rdata', 'rresp', 'rlast', 'rvalid']
            }
        },
        'sc_channel' : {
           'type' : 'axi_read',
           'param_cast' : None,
           'multicycle_types' : ['fixed_size', 'api_list_tracker',  'api_list_size']
        }
    },
    'axi_write' : {
        'parameters' : {
           'addr_t' : { 'datatype' : 'struct', 'default' : 'bit' },
           'data_t' : { 'datatype' : 'struct', 'default' : 'bit' },
           'strb_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'awaddr': 'addr_t',
            'awid' : 'bit [3:0]',
            'awlen' : 'bit [7:0]',
            'awsize' : 'bit [2:0]',
            'awburst' : 'bit [1:0]',
            'awvalid' : 'bool',
            'awready': 'bool',
            'wdata' : 'data_t',
            'wid': 'bit [3:0]',
            'wstrb' : 'strb_t',
            'wlast' : 'bool',
            'wvalid': 'bool',
            'wready' : 'bool',
            'bresp' : 'bit [1:0]',
            'bid' : 'bit [3:0]',
            'bvalid' : 'bool',
            'bready' : 'bool'
        },
        'modports' : {
            'src' : {
                'inputs' : ['awready', 'wready', 'bresp', 'bid', 'bvalid'],
                'outputs': ['awid', 'awaddr', 'awlen', 'awsize', 'awburst', 'awvalid', 'wid', 'wdata', 'wstrb', 'wlast', 'wvalid', 'bready']
            },
            'dst' : {
                'inputs' : ['awid', 'awaddr', 'awlen', 'awsize', 'awburst', 'awvalid', 'wid', 'wdata', 'wstrb', 'wlast', 'wvalid', 'bready'],
                'outputs': ['awready', 'wready', 'bresp', 'bid', 'bvalid']
            }
        },
        'sc_channel' : {
           'type' : 'axi_write',
           'param_cast' : None,
           'multicycle_types' : ['fixed_size', 'api_list_tracker',  'api_list_size']
        },
    },
    'axi4_stream' : {
        'parameters' : {
           'tdata_t' : { 'datatype' : 'struct', 'default' : 'bit' },
           'tid_t' : { 'datatype' : 'struct', 'default' : 'bit' },
           'tdest_t' : { 'datatype' : 'struct', 'default' : 'bit' },
           'tuser_t' : { 'datatype' : 'struct', 'default' : 'bit' }
        },
        'signals' : {
            'tvalid' : 'bool',
            'tready' : 'bool',
            'tdata' : 'tdata_t',
            'tstrb' : 'tdata_t',
            'tkeep' : 'tdata_t',
            'tlast' : 'bool',
            'tid' : 'tid_t',
            'tdest' : 'tdest_t',
            'tuser' : 'tuser_t'
        },
        'modports' : {
            'src' : {
                'inputs' : ['tready'],
                'outputs': ['tvalid', 'tdata', 'tstrb', 'tkeep', 'tlast', 'tid', 'tdest', 'tuser']
            },
            'dst' : {
                'inputs' : ['tvalid', 'tdata', 'tstrb', 'tkeep', 'tlast', 'tid', 'tdest', 'tuser'],
                'outputs': ['tready']
            }
        },
        'sc_channel' : {
           'type' : 'axi4_stream',
           'param_cast' : None,
           'multicycle_types' : ['fixed_size', 'api_list_tracker',  'api_list_size']
        },
    }
}
