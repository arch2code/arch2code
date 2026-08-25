# GENERATED_CODE_PARAM --block=producer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axiRd0': {
        "port": 'axiRd0',
        "name": 'producer.axiRd0',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiWr0': {
        "port": 'axiWr0',
        "name": 'producer.axiWr0',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = ()
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
