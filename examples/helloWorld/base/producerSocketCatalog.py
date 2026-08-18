# GENERATED_CODE_PARAM --block=producer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'test_rdy_vld': {
        "port": 'test_rdy_vld',
        "name": 'producer.test_rdy_vld',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'test_req_ack': {
        "port": 'test_req_ack',
        "name": 'producer.test_req_ack',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'test_push_ack': {
        "port": 'test_push_ack',
        "name": 'producer.test_push_ack',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'test_pop_ack': {
        "port": 'test_pop_ack',
        "name": 'producer.test_pop_ack',
        "interfaceType": 'pop_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'producer.test_rdy_vld',
    'producer.test_req_ack',
    'producer.test_push_ack',
    'producer.test_pop_ack',
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
