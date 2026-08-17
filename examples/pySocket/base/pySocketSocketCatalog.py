# GENERATED_CODE_PARAM --block=pySocket
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'test_req_ack': {
        "port": 'test_req_ack',
        "name": 'pySocket.test_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'test2Python_req_ack': {
        "port": 'test2Python_req_ack',
        "name": 'pySocket.test2Python_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dut2Python_req_ack': {
        "port": 'dut2Python_req_ack',
        "name": 'pySocket.dut2Python_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'test_push_ack': {
        "port": 'test_push_ack',
        "name": 'pySocket.test_push_ack',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'test_pop_ack': {
        "port": 'test_pop_ack',
        "name": 'pySocket.test_pop_ack',
        "interfaceType": 'pop_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dut2Python_push_ack': {
        "port": 'dut2Python_push_ack',
        "name": 'pySocket.dut2Python_push_ack',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'dut2Python_pop_ack': {
        "port": 'dut2Python_pop_ack',
        "name": 'pySocket.dut2Python_pop_ack',
        "interfaceType": 'pop_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'test_notify_ack': {
        "port": 'test_notify_ack',
        "name": 'pySocket.test_notify_ack',
        "interfaceType": 'notify_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dut2Python_notify_ack': {
        "port": 'dut2Python_notify_ack',
        "name": 'pySocket.dut2Python_notify_ack',
        "interfaceType": 'notify_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'test_rdy_vld': {
        "port": 'test_rdy_vld',
        "name": 'pySocket.test_rdy_vld',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dut2Python_rdy_vld': {
        "port": 'dut2Python_rdy_vld',
        "name": 'pySocket.dut2Python_rdy_vld',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'pySocket.test_req_ack',
    'pySocket.test2Python_req_ack',
    'pySocket.dut2Python_req_ack',
    'pySocket.test_push_ack',
    'pySocket.test_pop_ack',
    'pySocket.dut2Python_push_ack',
    'pySocket.dut2Python_pop_ack',
    'pySocket.test_notify_ack',
    'pySocket.dut2Python_notify_ack',
    'pySocket.test_rdy_vld',
    'pySocket.dut2Python_rdy_vld',
)
SYNC_NAMES = ()

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
