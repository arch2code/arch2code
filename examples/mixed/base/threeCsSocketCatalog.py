# GENERATED_CODE_PARAM --block=threeCs
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'see0': {
        "port": 'see0',
        "name": 'threeCs.see0',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'see1': {
        "port": 'see1',
        "name": 'threeCs.see1',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'see2': {
        "port": 'see2',
        "name": 'threeCs.see2',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'threeCs.see0',
    'threeCs.see1',
    'threeCs.see2',
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
