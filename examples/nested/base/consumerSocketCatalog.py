# GENERATED_CODE_PARAM --block=consumer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'src_trans_dest_trans_rv_tracker': {
        "port": 'src_trans_dest_trans_rv_tracker',
        "name": 'consumer.src_trans_dest_trans_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'src_clock_dest_trans_rv_tracker': {
        "port": 'src_clock_dest_trans_rv_tracker',
        "name": 'consumer.src_clock_dest_trans_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_clock_rv_tracker': {
        "port": 'src_trans_dest_clock_rv_tracker',
        "name": 'consumer.src_trans_dest_clock_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_trans_rv_size': {
        "port": 'src_trans_dest_trans_rv_size',
        "name": 'consumer.src_trans_dest_trans_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'src_clock_dest_trans_rv_size': {
        "port": 'src_clock_dest_trans_rv_size',
        "name": 'consumer.src_clock_dest_trans_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_clock_rv_size': {
        "port": 'src_trans_dest_clock_rv_size',
        "name": 'consumer.src_trans_dest_clock_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'consumer.src_trans_dest_trans_rv_tracker',
    'consumer.src_clock_dest_trans_rv_tracker',
    'consumer.src_trans_dest_clock_rv_tracker',
    'consumer.src_trans_dest_trans_rv_size',
    'consumer.src_clock_dest_trans_rv_size',
    'consumer.src_trans_dest_clock_rv_size',
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
