from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug

def postProcess(prj):
    """Post process the project after parsing the YAML file.

    Args:
        prj (project): The project object.
    """
    reg_interface = prj.addressControl.get('RegisterBusInterface', 'apbReg')
    file_gen = prj.a2cProj.get('fileGeneration', {})
    proj_file_gen = prj.proj.get('fileGeneration', {})
    # prefer users input else revert to default
    regBlockNaming = proj_file_gen.get('regBlockNaming', file_gen.get('regBlockNaming', {}))
    instance_prefix = regBlockNaming.get('instancePrefix', 'u_')
    block_suffix = regBlockNaming.get('blockSuffix', '_regs')
    # build a dictionary with sections and content the same as if it was parsed from a file
    #
    blocksWithRegisters = dict()
    for context, registers in prj.data['registers'].items():
        for register, registerData in registers.items():
            if registerData['blockKey'] not in blocksWithRegisters:
                blocksWithRegisters[registerData['blockKey']] = registerData['block']
    blocksWithMemories = dict()
    for context, memories in prj.data['memories'].items():
        for memory, memoryData in memories.items():
            if memoryData['regAccess'] and memoryData['blockKey'] not in blocksWithMemories:
                blocksWithMemories[memoryData['blockKey']] = memoryData['block']
    # create a dictionary of connections to be added to the database
    blocksNeedingConnections = blocksWithRegisters.copy()
    blocksNeedingConnections.update(blocksWithMemories)
        
    # create a set containers that hold address decode blocks, as blocks within the same scope of the decode can be connected directly
    decoderContainer = dict() # mapping of qualified container to qualified decoder instance
    instancesSimple = dict() # mapping of qualified instance to simple instance name
    groupDecoder = dict()
    primaryDecode = None
    primaryDecodeContainer = None
    for instance, instanceKey in prj.instances.items():
        instancesSimple[instanceKey] = instance

    reg_handler_blocks = dict()
    reg_handler_instances = dict()
    reg_handler_connection_maps = list()
    for block_key, block in blocksNeedingConnections.items():
        reg_block = block + block_suffix
        has_mdl = len(prj.hierKey[block_key]) > 0
        reg_handler_blocks[reg_block] = {'desc': block + ' Register handler',
                                         'isRegHandler': True,
                                         'hasVl': False,
                                         'hasRtl': True,
                                         'hasMdl': has_mdl,
                                         'hasTb': False,
                                         'isRegHandler': True}
        reg_handler_instances[instance_prefix + reg_block] = {'instanceType': reg_block,
                                                   'container': block}
        reg_handler_connection_maps.append({'interface': reg_interface,
                                            'block': block,
                                            'direction': 'dst',
                                            'instance': instance_prefix + reg_block})

    for addressGroup, groupData in prj.addressControl['AddressGroups'].items():
        if 'decoderInstance' in groupData:
            decoderInstance = groupData['decoderInstance']
            qualDecoderInstance = prj.instances[decoderInstance]
            groupDecoder[addressGroup] = qualDecoderInstance
            container = prj.instanceContainer[qualDecoderInstance]
            decoderContainer[container] = qualDecoderInstance
            if 'primaryDecode' in groupData:
                primaryDecode = qualDecoderInstance
                primaryDecodeContainer = container

    if primaryDecode is None:
        printWarning(f"no primary decode found. AddressGroups defined in {prj.proj['addressControl']} must have one address group defined as primaryDecode for register and memory access.")
        return

    # calculate the instances of the blocks keeping track of which instances are directly connectable to the address decode block
    instancesNeedingConnection = dict()
    instanceDirectConnection = dict()
    decoderContainerInstances = dict()
    for context, instances in prj.data['instances'].items():
        for instance, instanceData in instances.items():
            if instanceData['instanceTypeKey'] in blocksNeedingConnections:
                if instanceData['instanceTypeKey'] not in instancesNeedingConnection:
                    instancesNeedingConnection[instanceData['instanceTypeKey']] = dict()
                instancesNeedingConnection[instanceData['instanceTypeKey']][instance] = instanceData
                # is the instance in the same container as the address decode block
                if instanceData['containerKey'] in decoderContainer:
                    instanceDirectConnection[instanceData['instanceKey']] = True
                else:
                    instanceDirectConnection[instanceData['instanceKey']] = False
                    printError(f"Instances in address groups only supported at same level as decoder. Instance {instance} is in container {instanceData['containerKey']}.")
                    exit(warningAndErrorReport())
            if instanceData['instanceTypeKey'] in decoderContainer:
                if instanceData['instanceTypeKey'] not in decoderContainerInstances:
                    decoderContainerInstances[instanceData['instanceTypeKey']] = {instanceData['instanceKey']: instanceData}
                else:
                    decoderContainerInstances[instanceData['instanceTypeKey']][instanceData['instanceKey']] = instanceData

    connections = list()
    connectionMaps = list()
    listOfInstances = list()
    # build connections from decode blocks to blocks with registers and memories
    for block, blockData in instancesNeedingConnection.items():
        for instance, instanceData in blockData.items():
            connection = dict()
            instanceKey = instanceData['instanceKey']
            listOfInstances.append(instanceKey)
            if instanceDirectConnection[instanceKey]:
                if not instanceData.get('addressGroup'):
                    printError(f"Instance {instanceKey} needs to specify an address group for register address decode")
                    exit(warningAndErrorReport())
                connection['src'] = instancesSimple[groupDecoder[instanceData['addressGroup']]]
                connection['dst'] = instance
                connection['interface'] = reg_interface
                connection['srcport'] = "apb_"+instance
                connection['interfaceName'] = "apb_"+instance
                connections.append(connection)
            else:
                # for non direct connect cases we need to connect to parent in the same container as the address decode block
                # and create connectionMaps up through the hierarchy until we reach the parent in the same container as the address decode block
                # not implemented yet - will error above
                pass
    # build hierarchical connections between decoder blocks
    for container, decoder in decoderContainer.items():
        if decoder != primaryDecode:
            simpleContainerBlock = None
            for qualContainer, instanceData in decoderContainerInstances[container].items():
                # as there may be multiple instance of the block in question we need to create a decode interface for each one
                # as a channel from the higher level decoder to the contained lower level decoder
                connection = dict()
                listOfInstances.append(instanceData['instanceKey'])
                dst = instanceData['instance']
                src = instancesSimple[ decoderContainer[instanceData['containerKey']] ]
                simpleContainerBlock = instanceData['instanceType']
                connection['src'] = src
                connection['dst'] = dst
                connection['interface'] = reg_interface
                connection['srcport'] = "apb_"+dst
                connection['interfaceName'] = "apb_"+dst
                connections.append(connection)
            # there is a single connectionMap for each decoder container within the block
            connectionMap = dict()
            connectionMap['interface'] = reg_interface
            connectionMap['block'] = simpleContainerBlock
            connectionMap['direction'] = "dst"
            connectionMap['instance'] = instancesSimple[decoder]
            connectionMaps.append(connectionMap)
    ret = dict()
    ret['blocks'] = reg_handler_blocks
    ret['instances'] = reg_handler_instances
    ret['connections'] = connections
    ret['connectionMaps'] = connectionMaps
    ret['connectionMaps'].extend(reg_handler_connection_maps)
    prj.config.setConfig("INSTANCES_WITH_REGAPB", listOfInstances, bin=True )
    return ret