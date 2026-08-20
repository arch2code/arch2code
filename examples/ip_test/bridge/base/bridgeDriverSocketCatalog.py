# GENERATED_CODE_PARAM --block=bridgeDriver
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'out8': {
        "port": 'out8',
        "name": 'bridgeDriver.out8',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'out70': {
        "port": 'out70',
        "name": 'bridgeDriver.out70',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'bridgeDriver.out8',
    'bridgeDriver.out70',
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
