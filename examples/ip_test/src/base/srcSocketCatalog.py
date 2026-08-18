# GENERATED_CODE_PARAM --block=src
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'out0': {
        "port": 'out0',
        "name": 'src.out0',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'out1': {
        "port": 'out1',
        "name": 'src.out1',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'out2': {
        "port": 'out2',
        "name": 'src.out2',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'out3': {
        "port": 'out3',
        "name": 'src.out3',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'src.out0',
    'src.out1',
    'src.out2',
    'src.out3',
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
