# GENERATED_CODE_PARAM --block=producer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'src_trans_dest_trans_rv_tracker': {
        "port": 'src_trans_dest_trans_rv_tracker',
        "name": 'producer.src_trans_dest_trans_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'src_clock_dest_trans_rv_tracker': {
        "port": 'src_clock_dest_trans_rv_tracker',
        "name": 'producer.src_clock_dest_trans_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_clock_rv_tracker': {
        "port": 'src_trans_dest_clock_rv_tracker',
        "name": 'producer.src_trans_dest_clock_rv_tracker',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_trans_rv_size': {
        "port": 'src_trans_dest_trans_rv_size',
        "name": 'producer.src_trans_dest_trans_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'src_clock_dest_trans_rv_size': {
        "port": 'src_clock_dest_trans_rv_size',
        "name": 'producer.src_clock_dest_trans_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'src_trans_dest_clock_rv_size': {
        "port": 'src_trans_dest_clock_rv_size',
        "name": 'producer.src_trans_dest_clock_rv_size',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'producer.src_trans_dest_trans_rv_tracker',
    'producer.src_clock_dest_trans_rv_tracker',
    'producer.src_trans_dest_clock_rv_tracker',
    'producer.src_trans_dest_trans_rv_size',
    'producer.src_clock_dest_trans_rv_size',
    'producer.src_trans_dest_clock_rv_size',
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
