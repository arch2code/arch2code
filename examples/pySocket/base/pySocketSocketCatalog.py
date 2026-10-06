# GENERATED_CODE_PARAM --block=pySocket
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'test_req_ack': {
        "port": 'test_req_ack',
        "nameSuffix": '.test_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test2Python_req_ack': {
        "port": 'test2Python_req_ack',
        "nameSuffix": '.test2Python_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_req_ack': {
        "port": 'dut2Python_req_ack',
        "nameSuffix": '.dut2Python_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test_push_ack': {
        "port": 'test_push_ack',
        "nameSuffix": '.test_push_ack',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test_pop_ack': {
        "port": 'test_pop_ack',
        "nameSuffix": '.test_pop_ack',
        "interfaceType": 'pop_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_push_ack': {
        "port": 'dut2Python_push_ack',
        "nameSuffix": '.dut2Python_push_ack',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_pop_ack': {
        "port": 'dut2Python_pop_ack',
        "nameSuffix": '.dut2Python_pop_ack',
        "interfaceType": 'pop_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test_notify_ack': {
        "port": 'test_notify_ack',
        "nameSuffix": '.test_notify_ack',
        "interfaceType": 'notify_ack',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_notify_ack': {
        "port": 'dut2Python_notify_ack',
        "nameSuffix": '.dut2Python_notify_ack',
        "interfaceType": 'notify_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test_rdy_vld': {
        "port": 'test_rdy_vld',
        "nameSuffix": '.test_rdy_vld',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_rdy_vld': {
        "port": 'dut2Python_rdy_vld',
        "nameSuffix": '.dut2Python_rdy_vld',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
    'test_axi4_stream': {
        "port": 'test_axi4_stream',
        "nameSuffix": '.test_axi4_stream',
        "interfaceType": 'axi4_stream',
        "direction": 'src',
        "role": 'drive',
        "observeSuffix": None,
    },
    'dut2Python_axi4_stream': {
        "port": 'dut2Python_axi4_stream',
        "nameSuffix": '.dut2Python_axi4_stream',
        "interfaceType": 'axi4_stream',
        "direction": 'dst',
        "role": 'drive',
        "observeSuffix": None,
    },
}

LISTEN_SUFFIXES = (
    '.test_req_ack',
    '.test2Python_req_ack',
    '.dut2Python_req_ack',
    '.test_push_ack',
    '.test_pop_ack',
    '.dut2Python_push_ack',
    '.dut2Python_pop_ack',
    '.test_notify_ack',
    '.dut2Python_notify_ack',
    '.test_rdy_vld',
    '.dut2Python_rdy_vld',
    '.test_axi4_stream',
    '.dut2Python_axi4_stream',
)
SYNC_NAMES = ()

def required_names(instance):
    return [instance + suffix for suffix in LISTEN_SUFFIXES] + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port, instance):
    return instance + CATALOG[port]["nameSuffix"]

def observe_name_for_port(port, instance):
    suffix = CATALOG[port]["observeSuffix"]
    return None if suffix is None else instance + suffix

# GENERATED_CODE_END
