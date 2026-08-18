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
    'axiRd1': {
        "port": 'axiRd1',
        "name": 'producer.axiRd1',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiRd2': {
        "port": 'axiRd2',
        "name": 'producer.axiRd2',
        "interfaceType": 'axi_read',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiRd3': {
        "port": 'axiRd3',
        "name": 'producer.axiRd3',
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
    'axiWr1': {
        "port": 'axiWr1',
        "name": 'producer.axiWr1',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiWr2': {
        "port": 'axiWr2',
        "name": 'producer.axiWr2',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiWr3': {
        "port": 'axiWr3',
        "name": 'producer.axiWr3',
        "interfaceType": 'axi_write',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiStr0': {
        "port": 'axiStr0',
        "name": 'producer.axiStr0',
        "interfaceType": 'axi4_stream',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'axiStr1': {
        "port": 'axiStr1',
        "name": 'producer.axiStr1',
        "interfaceType": 'axi4_stream',
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
