# GENERATED_CODE_PARAM --block=consumer
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axiRd0': {
        "port": 'axiRd0',
        "name": 'consumer.axiRd0',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiRd0_obs',
    },
    'axiRd1': {
        "port": 'axiRd1',
        "name": 'consumer.axiRd1',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiRd1_obs',
    },
    'axiRd2': {
        "port": 'axiRd2',
        "name": 'consumer.axiRd2',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiRd2_obs',
    },
    'axiRd3': {
        "port": 'axiRd3',
        "name": 'consumer.axiRd3',
        "interfaceType": 'axi_read',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiRd3_obs',
    },
    'axiWr0': {
        "port": 'axiWr0',
        "name": 'consumer.axiWr0',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiWr0_obs',
    },
    'axiWr1': {
        "port": 'axiWr1',
        "name": 'consumer.axiWr1',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiWr1_obs',
    },
    'axiWr2': {
        "port": 'axiWr2',
        "name": 'consumer.axiWr2',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiWr2_obs',
    },
    'axiWr3': {
        "port": 'axiWr3',
        "name": 'consumer.axiWr3',
        "interfaceType": 'axi_write',
        "direction": 'dst',
        "role": 'drive',
        "observeName": 'consumer.axiWr3_obs',
    },
    'axiStr0': {
        "port": 'axiStr0',
        "name": 'consumer.axiStr0',
        "interfaceType": 'axi4_stream',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'axiStr1': {
        "port": 'axiStr1',
        "name": 'consumer.axiStr1',
        "interfaceType": 'axi4_stream',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'consumer.axiRd0',
    'consumer.axiRd1',
    'consumer.axiRd2',
    'consumer.axiRd3',
    'consumer.axiWr0',
    'consumer.axiWr1',
    'consumer.axiWr2',
    'consumer.axiWr3',
    'consumer.axiStr0',
    'consumer.axiStr1',
    'consumer.axiRd0_obs',
    'consumer.axiRd1_obs',
    'consumer.axiRd2_obs',
    'consumer.axiRd3_obs',
    'consumer.axiWr0_obs',
    'consumer.axiWr1_obs',
    'consumer.axiWr2_obs',
    'consumer.axiWr3_obs',
)
SYNC_NAMES = (
    'pysocket_sync',
)

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
