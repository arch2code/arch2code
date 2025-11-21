from typing import Dict, OrderedDict
import pysrc.arch2codeGlobals as g
from pysrc.yamlInclude import YAML
from pysrc.arch2codeHelper import printError, printWarning, printTracebackStack, warningAndErrorReport, printIfDebug, roundup_pow2min4
from pysrc.schema import Schema
import ruamel.yaml as YAMLRAW
import sqlite3
import os
import re
import pickle
import math
import importlib
import importlib.util

continueOnError = False

# yaml = YAML(typ='safe', pure=True)
yaml = YAMLRAW.YAML(typ='rt')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def basePathRelative(fileName, existsError = True):
    modFile = os.path.join(g.yamlBasePath, fileName)
    if existsError:
        if not os.path.exists(modFile):
            printError(f"Unable to find {fileName}, {os.path.abspath(modFile)}")
            exit(warningAndErrorReport())
    return modFile


def existsLoad(myFile):
    if not os.path.exists(myFile):
        modFile = basePathRelative(myFile)
    else:
        modFile = myFile

    with open(modFile) as f:
        ret = yaml.load(f)

    return ret

dirMacros = None
def expandDirMacros(myFile):
    global dirMacros
    if not dirMacros:
        return myFile
    if myFile[0] == '$':
        # extract path before first /
        pathKey = myFile[1:].split('/', 1)[0]
        if pathKey in dirMacros:
            myFile = myFile.replace(f"${pathKey}", dirMacros[pathKey])
    return myFile

def expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, missingDirOk = False):
    global dirMacros
    fileStub = fileDefinition.get('name', '')

    basePathKey = fileDefinition.get('basePath', '')
    basePathAbs = dirMacros[basePathKey]
    if not os.path.exists(basePathAbs) and not missingDirOk:
        printError(f"path of {basePathAbs} does not exist")
    moduleDirAbs = os.path.abspath(os.path.join(basePathAbs, moduleDir))
    blockDir = fileDefinition.get('blockDir', False)
    if blockDir:
        moduleDirAbs = os.path.join(moduleDirAbs, module)
    fileName = f"{moduleFileStub}{fileStub}"
    filePath = os.path.join(moduleDirAbs, fileName)
    return filePath

# if yaml file exists load it, otherwise return empty dict
def loadIfExists(myFile):
    if not os.path.exists(myFile):
        return {}
    with open(myFile) as f:
        ret = yaml.load(f)
    return ret

def resolveFilePath(userDict, a2cDict, key, basePath):
    filePath = ''
    if key in userDict:
        filePath = userDict[key]
    elif key in a2cDict:
        filePath = a2cDict[key]
    filePath = expandDirMacros(filePath)
    return filePath

def camelCase(*words):
    # convert to camelCase leaving first letter
    out = words[0] # we dont want to capitalize the first word by force
    if len(words) > 1:
        for word in words[1:]:
            wordStr = str(word) # make sure input is a string
            if len(wordStr) > 1:
                out = out + wordStr[0].upper() + wordStr[1:]
            elif len(wordStr) == 1:
                out = out + wordStr[0].upper()
            #no need for empty sting case
    return out

def getKeyPriority(data, prioritylist):
    for key in prioritylist:
        ret = data.get(key, None)
        # filter out empty strings or missing values
        if ret:
            return ret
    return None

def getPortChannelName(row, portKeyName = 'port'):
    return getKeyPriority(row, [portKeyName, 'name', 'interface'])

def loadModule(filename):
    module = None
    if not os.path.exists(filename):
        printError(f"Unable to find {filename}")
        exit(warningAndErrorReport())
    else:
        # we are importing a python lib
        spec = importlib.util.spec_from_file_location(os.path.splitext(filename)[0], filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module

# all the project specific stuff is handled in the config class
# this is stored in database during projectCreate and retrieved later by projectOpen
# useful stuff for the generators are stored here
class config:
    data = dict()
    modeRO = True
    def __init__(self, RO = True) -> None:
        self.modeRO = RO
        if not g.cur:
            g.cur = g.db.cursor()
        if not self.modeRO:
            sql = "CREATE TABLE IF NOT EXISTS _config (item, value BLOB, context, bin integer)"
            g.cur.execute(sql)
        sql = "SELECT * from _config"
        g.cur.execute(sql)
        data = g.cur.fetchall()
        for row in data:
            if row['bin']:
                self.data[row['item']] = pickle.loads(row['value'])
            else:
                self.data[row['item']] = row['value']

    # allows storing of strings or binary objects
    def setConfig(self, item, value, bin=False):
        if self.modeRO:
            printError(f"Attempt to write {item} in config in RO mode")
            exit(warningAndErrorReport())
        if isinstance(value, dict) or isinstance(value, list):
            bin = True
        if not bin:
            self.data[item] = value
            sql = f"INSERT OR REPLACE INTO _config (item, value, context, bin) VALUES ('{item}', '{value}', '', FALSE)"
            g.cur.execute(sql)
        else:
            # binary objects are 'pickled' to store them
            pdata = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
            g.cur.execute(f"INSERT OR REPLACE INTO _config (item, value, context, bin) values ('{item}', ?, '', TRUE)", (sqlite3.Binary(pdata), ))

    def getConfig(self, item, failOk = False):
        if item not in self.data:
            if failOk:
                return None
            printError(f"Invalid config item {item} not found, or its a binary object")
            value=None
        else:
            value = self.data[item]
        return value


    def delConfig(self, item):
        if self.modeRO:
            printError(f"Attempt to delete {item} in config in RO mode")
            exit(warningAndErrorReport())
        self.data.pop(item)
        sql = f"DETELE FROM _config where item = '{item}'"
        g.cur.execute(sql)

    def clearConfig(self):
        if self.modeRO:
            printError(f"Attempt to clear config in RO mode")
            exit(warningAndErrorReport())
        self.data=dict()
        sql = f"DROP TABLE IF EXISTS _config"
        g.cur.execute(sql)

# hierarchy is defined by who contains who, or who is my parent
# this prevents the need for nested definition
def generateHierarchy(inputInstances, inputBlocks, withContext = False ):
    instances = dict()
    blocks = dict()
    hier = dict()
    hierKey = dict()
    instanceContainer = dict()
    if not withContext:
        # if we are being called from projectCreate, the input dictionaries do not have additional context depth
        # so we need to make it compatible to avoid a bunch of conditionals, and then operate as if it is the nested case
        instanceLoop = {"dummy": inputInstances}
        blockLoop = {"dummy": inputBlocks}
    else:
        instanceLoop = inputInstances
        blockLoop = inputBlocks
    for context, contextInstances in instanceLoop.items():
        for qualInst, row in contextInstances.items():
            container = row['container']
            containerKey = row['containerKey']
            instance = row['instance']
            instanceType = row['instanceType']
            instanceTypeKey = row['instanceTypeKey']
            # the two calling use cases (withContext) are slightly different so use get with fallback to loop key
            instanceKey = row.get('instanceKey', qualInst)
            if instance in instances:
                # duplicate name
                if not isinstance(instances[instance], dict):
                    # this entry is not a dict, so convert it to one
                    temp = instances[instance]
                    instances[instance] = { temp: None}
                instances[instance][instanceKey] = None
            else:
                instances[instance] = instanceKey
            #ensure both parent and child are in the map
            if instanceType not in hier:
                hier[instanceType] = OrderedDict()
            if instanceTypeKey not in hierKey:
                hierKey[instanceTypeKey] = OrderedDict()
            # topInstance is a special case that does not have a container as it is the root of the hierarchy
            if container != "_topInstance":
                if container not in hier:
                    hier[container] = OrderedDict()
                if containerKey not in hierKey:
                    hierKey[containerKey] = OrderedDict()
                hier[container][instance] = row
                hierKey[containerKey][instanceKey] = row
                blocks[container] = containerKey
                instanceContainer[instanceKey] = containerKey
    # create block to blockKey mapping
    for context, contextBlocks in blockLoop.items():
        for qualBlock, row in contextBlocks.items():
            block = row['block']
            # the two calling use cases are slightly different
            blockKey = row.get('blockKey', qualBlock)
            if block in blocks:
                if not isinstance(blocks[block], dict):
                    blocks[block] = {blocks[block]: None}
                blocks[block][blockKey] = None
            blocks[block] = blockKey
    return (hier, hierKey, instances, instanceContainer, blocks)

# project open is the class that loads the database and provides access to the data
# it is used by the generators to access the data
# it additionaly provides some helper functions to make the generators easier to write
# the database contents are stored in the data dict in manner similar to the schema
class projectOpen:
    data = dict() # all database derived data lives here. key = table name. Format corresponds to the schema
    data_by_parent = dict() # nested tables indexed by parent storage key for efficient child lookup
    tables = None
    config = None
    schema = None
    specialContexts = {"_global", "_a2csystem"} # special contexts that should be excluded from includes
    hier = dict()
    hierKey = dict()
    instances = dict() # mapping of instance names (user friendly) to qualified instance names (unique)
    blocks = dict() # mapping of block names (user friendly) to qualified block names (unique)
    rangeOfInstances = dict() # mapping of instance names (user friendly) of only a selected range
    connections = dict() # mapping of connections between the rangeOfInstances
    connectionMaps = dict() # mapping of connectionMaps in rangeOfInstances
    blockContainedConnection = dict()
    yamlContext = dict()
    includeName = dict()
    instanceContainer = None
    filemap = None
    def __init__(self, dbFile) -> None:
        if not os.path.exists(dbFile):
            printError(f"{dbFile} does not exist")
            exit(warningAndErrorReport())
        # for open we open the database read only to allow concurrency via makefile
        openString = f"file:{dbFile}?mode=ro"
        g.db = sqlite3.connect(openString, uri = True)
        if g.debug:
            # in debug mode, dont use the sqlite optimized row factory as its a pain in the debugger
            g.db.row_factory = dict_factory
        else:
            g.db.row_factory = sqlite3.Row
        g.cur = g.db.cursor()
        self.config = config()
        self.schema = Schema()
        self.tables = self.schema.get_table_names()
        g.yamlBasePath = self.config.getConfig('BASEYAMLPATH')
        self.yamlContext = self.config.getConfig('YAMLCONTEXT')
        self.includeName = self.config.getConfig('INCLUDENAME')
        self.filemap = self.config.getConfig('FILEMAP')
        global dirMacros
        dirMacros = self.config.getConfig('DIRS')
        printIfDebug("Data Loaded")
        self.loadData()
        self.generateHierarchy()
        printIfDebug("Project loaded")
    
    def getSchemaNode(self, table_name):
        """
        Get the schema Node object for a given table name.
        
        Args:
            table_name: Full table name (e.g., 'interface_defs', 'interface_defsmodports')
        
        Returns:
            Node object or None if not found
        """
        return self.schema.get_node(table_name)

    def loadData(self):
        # loop through the schema loading all the tables
        for table in self.schema.tables:
            printIfDebug("Loading table: "+table)
            # we need the key for the table
            if table in self.schema.data['comboKey']:
                # if the table was defined using a combo key, then use the key field as is
                # this prevents the issue of additional context making the same key not match - eg for connectionMaps we want matches
                # with connection even if the connection and connectionMap were defined in different files (common case)
                keyName = self.schema.data['key'][table]
            else:
                # otherwise use the context version to ensure uniqueness of entries
                keyName = self.schema.data['key'][table] + 'Key'

            # Load subtables recursively (depth-first) before loading the parent table
            if table in self.schema.data['subTable']:
                self._loadSubTablesRecursive(table, self.schema.data['schema'][table], keyName)

            self.loadTable(table, self.schema.data['schema'][table], keyName)
    
    def _loadSubTablesRecursive(self, parentTable, parentSchema, parentKeyName, parent_key_chain=None):
        """Recursively load all subtables depth-first
        
        Args:
            parent_key_chain: List of parent qualified key field names (e.g., ['interface_typeKey', 'modportKey'])
        """
        if parentTable not in self.schema.data['subTable']:
            return
        
        for subTable in self.schema.data['subTable'][parentTable]:
            printIfDebug(f"  Loading sub table: {subTable}")
            
            # Get the field name that holds this subtable in the parent schema
            subTableFieldName = self.schema.data['subTable'][parentTable][subTable]
            subTableSchema = parentSchema[subTableFieldName]
            
            # Get the key for this subtable
            subTableKey = self.schema.data['key'][subTable]
            
            # Build the extended parent key chain for this subtable
            # Use the auto-derived parent_key_chain from schema (should always be available after _finalize_schema)
            extended_chain = self.schema.data.get('parentKeyChain', {}).get(subTable, [])
            
            # Recursively load any nested subtables first (depth-first)
            self._loadSubTablesRecursive(subTable, subTableSchema, subTableKey, extended_chain)
            
            # Now load this subtable with the full parent key chain
            self.loadTable(subTable, subTableSchema, subTableKey, parent_key_chain=extended_chain)

    def _reconstruct_nested_structure(self):
        """
        Reconstruct the nested dictionary structure by attaching loaded subtables
        back to their parent tables.
        
        This runs after all tables are loaded. For each top-level table, we walk
        through and attach its nested tables.
        """
        printIfDebug("Reconstructing nested structure...")
        print(f"DEBUG: Schema tables = {self.schema.tables}")
        print(f"DEBUG: Schema subTable keys = {list(self.schema.data['subTable'].keys())}")
        
        # Process each top-level table
        for table in self.schema.tables:
            if table in self.schema.data['subTable']:
                print(f"DEBUG: Processing top-level table '{table}' with subtables: {list(self.schema.data['subTable'][table].keys())}")
                self._attach_subtables_recursive(table, self.data[table], self.schema.data['schema'][table])
    
    def _attach_subtables_recursive(self, parentTable, parentData, parentSchema):
        """
        Recursively attach subtables to their parent entries.
        
        Args:
            parentTable: Name of the parent table
            parentData: Dict of parent table entries
            parentSchema: Schema definition for parent table
        """
        if parentTable not in self.schema.data['subTable']:
            return
        
        for subTable in self.schema.data['subTable'][parentTable]:
            subTableFieldName = self.schema.data['subTable'][parentTable][subTable]
            subTableSchema = parentSchema[subTableFieldName]
            subTableData = self.data.get(subTable, {})
            
            if not subTableData:
                continue
            
            # For each parent entry, find and attach its child entries
            for parentKey, parentEntry in parentData.items():
                # Build the grouping key for this parent
                # Get the parent's qualified key fields that children reference
                parent_key_chain = self.schema.data.get('parentKeyChain', {}).get(subTable, [])
                
                if parent_key_chain:
                    # Build the composite grouping key from parent's qualified key fields
                    # Example: for modportGroups with parent_key_chain=['modportKey'],
                    # we need parentEntry['modportKey'] value
                    composite_parts = []
                    for pk_field in parent_key_chain:
                        if pk_field in parentEntry:
                            composite_parts.append(str(parentEntry[pk_field]))
                        else:
                            # Parent doesn't have this key field, skip
                            break
                    
                    if len(composite_parts) == len(parent_key_chain):
                        grouping_key = '/'.join(composite_parts)
                    else:
                        continue
                else:
                    # No parent key chain, use parent's own key
                    grouping_key = parentKey
                
                # Find all child entries that belong to this parent
                # Child entries were grouped by composite key during loading
                children = {}
                for childKey, childEntry in subTableData.items():
                    # Skip if childEntry is not a dict (shouldn't happen but be defensive)
                    if not isinstance(childEntry, dict):
                        continue
                    
                    # Check if this child belongs to this parent
                    # The child's grouping key should match or start with parent's grouping_key
                    if parent_key_chain:
                        # Build child's grouping key from its parent key fields
                        child_composite_parts = []
                        for pk_field in parent_key_chain:
                            if pk_field in childEntry:
                                child_composite_parts.append(str(childEntry[pk_field]))
                        
                        if child_composite_parts:
                            child_grouping_key = '/'.join(child_composite_parts)
                            if child_grouping_key == grouping_key:
                                # Extract the child's own key (without parent keys)
                                child_own_key = childEntry.get(self.schema.data['key'][subTable])
                                if child_own_key:
                                    children[child_own_key] = childEntry
                    else:
                        # Simple case: child has outerkey matching parent key
                        outerkey_field = None
                        for field_name, field_type in subTableSchema.items():
                            if field_type == 'outerkey':
                                outerkey_field = field_name
                                break
                        
                        if outerkey_field and childEntry.get(outerkey_field) == parentEntry.get(outerkey_field):
                            child_own_key = childEntry.get(self.schema.data['key'][subTable])
                            if child_own_key:
                                children[child_own_key] = childEntry
                
                # Attach children to parent if any found
                if children:
                    parentEntry[subTableFieldName] = children
                    
                    # Recursively process these children's subtables
                    self._attach_subtables_recursive(subTable, children, subTableSchema)

    # when parent_key_chain is None we are just creating a simple dictionary
    # when parent_key_chain is not none then the records should be grouped under composite parent key for later reassembly
    def loadTable(self, tableName, schema, keyName, parent_key_chain=None):
        """
        Load table from database and build dict structure
        
        Args:
            tableName: Name of the table to load
            schema: Schema definition for this table
            keyName: The anchor field name (e.g., 'interface_type')
            parent_key_chain: List of qualified parent key fields for composite grouping
                             (e.g., ['interface_typeKey', 'modportKey'])
        """
        
        attrib = self.schema.data['attrib'].get(tableName, [])
        columns = schema.copy()
        # figure out which mode to use
        if 'list' in attrib:
            listMode = True
        else:
            listMode = False
        innerKey = ''
        if 'multiple' in attrib:
            multi = True
            # for multi case we are adding as a dict, so need to figure out how to group the records ie what is the dict key
            # Query the schema directly instead of searching through columns
            innerKey = self.schema.data['key'].get(tableName, '')
            if innerKey == '':
                printError(f"For table {tableName} inner key not specified in schema")
                exit(warningAndErrorReport())

        else:
            multi = False
        myTable = OrderedDict()

        node = self.getSchemaNode(tableName)
        if not node:
            printError(f"Table {tableName} has no Node object in schema - this should not happen")
            exit(warningAndErrorReport())
        storage_key_field_qualified = node.get_storage_key_field_name_qualified()
        storage_key_field = node.get_storage_key_field_name()
        sql = f'SELECT * from {tableName} ORDER BY rowid'
        # Get parent storage key field name for data_by_parent indexing (only for nested tables)
        parent_key_field = node.get_parent_storage_key_field_name()
        if not node or not node.storage_key_field_qualified:
            raise ValueError(
                f"Cannot lookup children for table '{tableName}': "
                f"node.storage_key_field_qualified not configured. "
                f"This indicates a schema configuration error."
            )
            
        g.cur.execute(sql)
        data = g.cur.fetchall()
        firstRow = True
        previousKey = ''
        myList = list()
        myMulti = OrderedDict()
        myRow = dict()
        
        for row in data:
            # Build the composite key for storing this row
            
            # Use Node's method to build storage key for nested tables with parent chains
            # For top-level tables (parent_key_chain is None), use simple key
            newKey = node.build_storage_key(row)
                
            #to deal with lists/nested dicts we need to create record only when the key changes
            if newKey != previousKey:
                if not firstRow:
                    if listMode:
                        myTable[previousKey] = myList
                        myList = list()
                    elif multi:
                        # Multi-entry: individual entries stored per-row, no grouping needed
                        pass
                    else:
                        myTable[previousKey] = myRow
                else:
                    firstRow = False
                myRow = dict()
                previousKey = newKey
            # now go through the row and create the dict
            for col in columns:
                if isinstance(columns[col], dict):
                    # this is a subtable - need to look it up from the already-loaded subtable data
                    subtable_name = tableName + col
                    
                    # Use parent-indexed structure if available
                    if subtable_name in self.data_by_parent:
                        # data_by_parent is always indexed by the qualified parent storage key
                        # Use the precomputed qualified field name from the node
                        lookup_key = row[node.storage_key_field_qualified]
                        myRow[col] = self.data_by_parent[subtable_name].get(lookup_key, None)
                    else:
                        # Top-level tables - use primary data structure
                        subtable_node = self.getSchemaNode(subtable_name)
                        if not subtable_node:
                            printError(f"Subtable {subtable_name} has no Node object in schema - this should not happen")
                            exit(warningAndErrorReport())
                        subtable_lookup_key = subtable_node.build_storage_key(row)
                        myRow[col] = self.data[subtable_name].get(subtable_lookup_key, None)
                else:
                    myRow[col] = row[col]
            
            # For multi-entry tables, ensure the innerKey is in myRow
            # (it might have been excluded from columns if it was myKeyName)
            if multi and innerKey and innerKey not in myRow:
                myRow[innerKey] = row[innerKey]
                
            if listMode:
                myList.append(myRow)
                myRow = dict()
            if multi:
                # For multi-entry tables, store individual entries in myTable using qualified keys
                # and also build grouped structure for nested access
                
                # Determine the qualified key for top-level storage (use row, not myRow)
                top_level_key = row[node.storage_key_field_qualified]
                
                # Store individual entry in top-level table
                myTable[top_level_key] = myRow
                
                # Also build parent-indexed structure if this is a nested table
                if parent_key_field:
                    # Check if the parent key field exists in the row (try-except for sqlite3.Row compatibility)
                    try:
                        parent_storage_key = row[parent_key_field]
                        
                        if tableName not in self.data_by_parent:
                            self.data_by_parent[tableName] = {}
                        if parent_storage_key not in self.data_by_parent[tableName]:
                            self.data_by_parent[tableName][parent_storage_key] = {}
                        
                        # Index by anchor field for user-friendly nested access (e.g., 'src', 'dst')
                        # or by storage key for combo/collapsed tables (e.g., 'blockAaStuffIf')
                        if node and node.anchor_field:
                            nested_index_key = myRow[node.anchor_field]
                        else:
                            # For tables without anchor (combo/collapsed), use storage key value
                            nested_index_key = myRow[innerKey]
                        self.data_by_parent[tableName][parent_storage_key][nested_index_key] = myRow
                    except (KeyError, IndexError) as e:
                        # Parent key field not in this row (shouldn't happen for properly configured nested tables)
                        raise ValueError(
                            f"Failed to build data_by_parent for table '{tableName}': {e}. "
                            f"parent_key_field='{parent_key_field}', "
                            f"This indicates a schema configuration error or missing parent key in row."
                        )
                
                myRow = dict()
        # the last record may need to be added
        if not firstRow:
            if listMode:
                myTable[previousKey] = myList
            elif multi:
                # Multi-entry: already stored individual entries, nothing to do
                pass
            else:
                myTable[previousKey] = myRow

        self.data[tableName] = myTable

    # hierarchy is defined by who contains who, or who is my parent
    # this prevents the need for nested definition
    def generateHierarchy(self):
        (hier, hierKey, qualInstances, instanceContainer, blocks) = generateHierarchy(self.data['instances'], self.data['blocks'])
        self.hier = hier
        self.hierKey = hierKey
        self.instances = qualInstances
        self.instanceContainer = instanceContainer
        self.blocks = blocks

    def getQualTop(self, instanceTop):
        if instanceTop==g.defaultInstance:
            instanceTop = self.config.getConfig('TOPINSTANCE')
        # top instance may be a fully qualified name already - check

        return self.getQualInstance(instanceTop)

    # instance maybe qualified or not, make sure it is
    def getQualInstance(self, instance):
        # top instance may be a fully qualified name already - check
        if instance in self.data['instances']:
            qual = instance
        else:
            #its not a fully qualified name so lets try and convert
            qual = self.qualInstance(instance)
            if isinstance(qual, dict):
                printError(f"The instance specified: {instance} is not a unique instance in the design.\nPlease use a unique instance or a fully qualified instance name instead. Possible fully qualified names for specified instance are:")
                for inst in qual:
                    printWarning(inst)
                exit(warningAndErrorReport())
        return qual

    # convert map of instances
    def getQualInstances(self, instances):
        ret = dict()
        for inst in instances:
            ret[self.getQualInstance(inst)] = 0
        return ret

    # instance maybe qualified or not, make sure it is
    def getQualBlock(self, block):
        # top instance may be a fully qualified name already - check
        if block in self.data['blocks']:
            qual = block
        else:
            if block not in self.blocks:
                printError(f"The block specified: {block} does not exist in the design")
                exit(warningAndErrorReport())
            #its not a fully qualified name so lets try and convert
            if isinstance(self.blocks[block], dict):
                printError(f"The block specified: {block} is not a unique instance in the design.\nPlease use a unique or a fully qualified block name instead. Possible fully qualified names are:")
                for myBlock in self.blocks[block]:
                    printWarning(myBlock)
                exit(warningAndErrorReport())
            qual = self.blocks[block]
        return qual

    def getModuleFilename(self, filekey, module, fileType):
        fileDefinition = self.filemap.get(filekey, None)
        if not fileDefinition:
            printError(f"File type {filekey} not defined in project file filemap section")
            exit(warningAndErrorReport())
        fileStub = fileDefinition.get('name', '')
        extension = fileDefinition['ext'].get(fileType, None)
        if not extension:
            printError(f"File type {fileType} not defined in filemap->ext")
            exit(warningAndErrorReport())
        fileName = f"{module}{fileStub}.{extension}"
        return fileName

    def _build_enum_lookup(self):
        """Build a lookup dictionary for enum values (lazy initialization)"""
        if hasattr(self, '_enum_lookup'):
            return
        
        self._enum_lookup = {}
        
        # Build lookup from typesenum table
        # typesenum is organized as: {'enumType/file.yaml': [list of enum entries]}
        # Each enum entry has 'enumName' and 'value' fields
        if 'typesenum' in self.data:
            for enum_type_key, enum_list in self.data['typesenum'].items():
                if isinstance(enum_list, list):
                    for enum_entry in enum_list:
                        if isinstance(enum_entry, dict):
                            enum_name = enum_entry.get('enumName')
                            enum_value = enum_entry.get('value')
                            context = enum_entry.get('_context', '')
                            
                            if enum_name and context and enum_value is not None:
                                qual_enum_name = f"{enum_name}/{context}"
                                self._enum_lookup[qual_enum_name] = enum_value
    
    def getConst(self, value):
        try:
            ret = int(value)
        except:
            ret = None
            
            # First, try to look up in constants table using qualified key
            if 'constants' in self.data and value in self.data['constants']:
                const_data = self.data['constants'][value]
                if isinstance(const_data, dict):
                    ret = const_data.get('value', None)
            
            # If not found in constants, look up in enum lookup dictionary
            if ret is None:
                # Build enum lookup on first use (lazy initialization)
                self._build_enum_lookup()
                ret = self._enum_lookup.get(value, None)
            
            if ret is None:
                printError(f"Unknown constant '{value}'")
                exit(warningAndErrorReport())
        return ret


    # based on a block get the sub hier tree
    def getSubHier(self, topBlock):
        startBlock = self.getQualBlock(topBlock)
        ret = dict()
        nextLoop = dict()
        ret[startBlock] = 0
        nextLoop[startBlock] = self.hierKey[startBlock]
        while nextLoop:
            todo = nextLoop
            nextLoop = dict()
            for block,instances in todo.items():
                for instance, instanceValue in instances.items():
                    if instanceValue['instanceTypeKey'] not in ret:
                        nextLoop[instanceValue['instanceTypeKey']] = self.hierKey[instanceValue['instanceTypeKey']]
                        ret[instanceValue['instanceTypeKey']] = 0

        #for block in
        return ret

    # based on the list of contexts provided generate easy accessable structure for jinja
    # dataTypeMapping is a list ordered by maxSize which is used to map into platform specific types
    # each list entry should be a dict having the following required and optional keys
    #          'maxSize' : required - field indicating the largest bit width supported
    #             'type' : required - platform specific type string eg bool
    #            'array' : optional - if bitwidth needs to be in an array eg pc largest size = 64 bit so an array is used intead
    # 'arrayElementSize' : optional - if array is used, how many bits per array
    def getContextData(self, contexts, dataTypeMapping):
        ret = dict()
        enums = dict()
        ret['includeContext'] = dict()
        includes = self.config.getConfig('INCLUDEFILES')
        ret['includeFiles'] = includes
        for context in contexts:
            if context not in self.yamlContext:
                printError(f"The context specified in GENERATED_CODE_PARAM: {context} is not a known context.\nPossible valid contexts are:")
                for myContext in self.yamlContext:
                    printWarning(myContext)
                exit(warningAndErrorReport())
            for k in self.yamlContext[context]:
                ret['includeContext'][k] = 0
        objects = ['constants', 'types', 'structures', 'encoders']
        ret['specialStructures'] = OrderedDict()
        for object in objects:
            ret[object] = OrderedDict()
            for key, value in self.data[object].items():
                if value['_context'] in contexts:
                    if object=='structures':
                        if key in self.data['specialStructures']:
                            ret['specialStructures'][key] = value
                        else:
                            ret[object][key] = value
                    if object=='constants':
                        ret[object][key] = value
                        if isinstance(value["value"], int):
                            isSigned = value["value"] < 0
                            if not isSigned and abs(value["value"]) <= 0xFFFFFFFF:
                                ret[object][key]['valueType'] = 'uint32_t'
                            elif isSigned and abs(value["value"]) <= 0x7FFFFFFF:
                                ret[object][key]['valueType'] = 'int32_t'
                            else:
                                ret[object][key]['valueType'] = 'int64_t' if isSigned else 'uint64_t'
                        else:
                            printError(f"Invalid constant type for {key}")
                            exit(warningAndErrorReport())
                    if object=='types':
                        if value['enum']:
                            enums[key] = value
                            enums[key]['descSpaces'] = max(0, 20-len(value['type']))
                            for myEnum in value['enum']:
                                enumLen = len(myEnum['enumName'])+len(str(myEnum['value']))
                                myEnum['descSpaces'] = max(0, 20-enumLen)
                        else:
                            ret[object][key] = value
                            bitwidth = self.getConst( value['width'] )
                            isSigned = value.get('isSigned', False)
                            # loop through ordered list
                            thisType = None
                            typeArraySize = 1
                            for myType in dataTypeMapping:
                                if bitwidth <= myType['maxSize']:
                                    arrayElementSize = myType.get('arrayElementSize', 0)
                                    if arrayElementSize > 0:
                                        # round up to the nearest multiple using integer div, plus one if there is a modulo non zero
                                        typeArraySize = bitwidth // arrayElementSize + (bitwidth % arrayElementSize > 0)
                                    # Select signed or unsigned type based on isSigned flag
                                    thisType = myType['signedType'] if isSigned else myType['unsignedType']
                                    #if we found something terminate the list as we want the smallest type
                                    break
                            if thisType is None:
                                printError(f"Unknown Bitwidth for {key}")
                                exit(warningAndErrorReport())
                            ret[object][key]['platformDataType'] = thisType
                            ret[object][key]['typeArraySize'] = typeArraySize
                            ret[object][key]['realwidth'] = bitwidth
                    if object=='encoders':
                        ret[object][key] = value
                        bits = int(value["totalBits"])
                        for itemKey, itemVal in value['items'].items():
                            if itemVal["numBitsKey"] !="":
                                entryBits = self.getConst(itemVal["numBitsKey"])
                            else:
                                entryBits = int(itemVal["numBits"])
                            encodingMask = ((1 << bits) - 1) ^ ((1 << entryBits) - 1)
                            itemVal['numBitsInt'] = entryBits
                            itemVal['encodingMask'] = encodingMask


        ret['enums'] = enums
        ret['context'] = context
        return ret

    # do some preproccessing to assemble subset of data easily accessed by Jinja
    # from perspective of qualBlock
    # subBlocks will be referenced if in the set of instances
    # this would be easier in SQL..
    def getBlockDataOld(self, qualBlock, instances, trimRegLeafInstance=False):
        blockDataSet = {'subBlockInstances', 'ports', 'registers', 'memories', 'memoryConnections', 'registerConnections', 'regPorts', 'connections', 'connectionMaps', 'subBlocks', 'includeContext', 'addressDecode', 'variants'}
        regDirection = { 'blk': { 'ro': 'src', 'rw': 'dst', 'ext': 'dst'}, 'reg': { 'ro': 'dst', 'rw': 'src', 'ext': 'src'}}
        ret = dict()
        structs = dict() # to capture where all the objects are defined
        consts = dict() # to capture where all the objects are defined
        # create allthe output containers
        includes = self.config.getConfig('INCLUDEFILES')
        ret['includeFiles'] = includes
        for k in blockDataSet:
            ret[k] = dict()
        ret['qualBlock'] = qualBlock
        ret['blockInfo'] = self.data['blocks'][qualBlock]
        ports = dict()
        regPorts = dict()
        addressDecoder = False # does the block need any address decode logic
        # identify which of the callers instances are instances of qualBlock and build a dict of them
        # also build the dict of all the contained instances
        qualBlockInstances = dict()
        qualBlockLeafInstance = None
        qualBlockLeafInstanceContainer = None

        # FIXME Until global code refactoring, we define the legacy 'registerLeafInstance' flag,
        #       based on the block based 'isRegHandler' flag of each instance
        for inst in instances:
            instBlock = self.data['instances'][inst]['instanceTypeKey']
            self.data['instances'][inst]['registerLeafInstance'] = self.data['blocks'][instBlock]['isRegHandler']

        for inst in instances:
            if self.data['instances'][inst]['instanceTypeKey'] == qualBlock:
                parentBlock = self.data['instances'][inst]['containerKey']
                qualBlockInstances[inst] = None
                qualBlockLeafInstance = self.data['instances'][inst]['registerLeafInstance']
                qualBlockLeafInstanceContainer = self.data['instances'][inst]['container']
                if self.data['instances'][inst]['variant'] != '':
                    filtered_variants_data = {k: v for k, v in self.data['parametersvariants'][qualBlock].items() if v.get('variant') == self.data['instances'][inst]['variant']}
                    ret['variants'][self.data['instances'][inst]['variant']] = filtered_variants_data
            if qualBlock in self.hierKey and inst in self.hierKey[qualBlock]:
                ret['subBlockInstances'][inst] = self.hierKey[qualBlock][inst]
        if len(qualBlockInstances) == 0:
            # there is no instance of the of type qualblock
            return None

        for mem, memInfo in self.data['memories'].items():
            if memInfo['blockKey'] == qualBlock:
                ret['memories'][mem] = memInfo
                structs[memInfo['structureKey']] = 0
                consts[memInfo['wordLinesKey']] = 0
                if memInfo['regAccess']:
                    addressDecoder = True # we have memories that need FW access

        for reg, regInfo in self.data['registers'].items():
            if regInfo['blockKey'] == qualBlock:
                ret['registers'][reg] = regInfo
                ret['registers'][reg]['bytes'] = (self.data['structures'][regInfo['structureKey']]['width'] + 7) >> 3 # round up to whole byte
                structs[regInfo['structureKey']] = 0
                addressDecoder = True #register = AddressDecoder

        # is this block a special apbDecode block type that performs abp bus routing
        isApbRouter = False
        addressConfig = self.config.getConfig('ADDRESS_CONFIG', True)
        if addressConfig:
            for addressGroup, addressGroupData in addressConfig.get('AddressGroups', {}).items():
                decoder = addressGroupData.get('decoderInstance', None)
                if decoder is not None:
                    qualDecoder = self.getQualInstance(decoder)
                    if qualDecoder in qualBlockInstances:
                        instanceWithRegApb = self.config.getConfig("INSTANCES_WITH_REGAPB", failOk=True)
                        if instanceWithRegApb is None:
                            printError('No instances with register interface found in db: missing or invalid register post processing script')
                            exit(warningAndErrorReport())
                        isApbRouter = True
                        ret['addressDecode']['addressGroupData'] = addressGroupData
                        ret['addressDecode']['addressGroup'] = addressGroup
                        ret['addressDecode']['containerBlock'] = self.instanceContainer[qualDecoder]
                        ret['addressDecode']['instanceWithRegApb'] = self.config.getConfig("INSTANCES_WITH_REGAPB", failOk=True)
        ret['addressDecode']['isApbRouter'] = isApbRouter
        # go through memory connections and collect if either src or dest
        for memConn, val in self.data['memoryConnections'].items():
            if val['blockKey'] == qualBlock:
                ret['memoryConnections'][memConn] = val
                if (val['instance'] != ''):
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = ''
                structs[self.data['memories'][val['memoryBlock']]['structureKey']] = 0
                consts[self.data['memories'][val['memoryBlock']]['wordLinesKey']] = 0
            if val['instanceKey'] in qualBlockInstances:
                ret['memoryConnections'][memConn] = val
                if (val['instance'] != ''):
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = ''
                structs[self.data['memories'][val['memoryBlock']]['structureKey']] = 0
                consts[self.data['memories'][val['memoryBlock']]['wordLinesKey']] = 0

        for regConn, val in self.data['registerConnections'].items():
            if val['blockKey'] == qualBlock:
                ret['registerConnections'][regConn] = val
                structs[regInfo['structureKey']] = 0
            if val['instanceKey'] in qualBlockInstances:
                ret['registerConnections'][regConn] = val
                structs[regInfo['structureKey']] = 0

        interfaces = OrderedDict()

        #connection are managed by the parent so we need to build the dict of connections contained within the qualBlock
        # loop through all the contained instances, and the in scope connections and copy the connection info
        for inst in ret['subBlockInstances']:
            for conn in self.connections[inst]:
                # is this connection to be considered in scope?
                if conn not in self.connections['_external']:
                    this = self.data['connections'][conn]
                    ret['connections'][conn] = this
                    # create jinja friendly names
                    # channel name is based on src port
                    if this['interfaceName']=='':
                        this['interfaceName'] = this['channel']
                    this['channelName'] = this['interfaceName']
                    this['interfaceType'] = self.data['interfaces'][this['interfaceKey']]['interfaceType']
                    for end, endVal in this['ends'].items():
                        endVal['name'] = endVal['portName']
                    if self.data['interfaces'][this['interfaceKey']]['structures']:
                        for structInfo in self.data['interfaces'][this['interfaceKey']]['structures']:
                            structs[structInfo['structureKey']] = 0
            if self.data['instances'][inst]['registerLeafInstance']:
                # create connection for apb leaf register module from registers
                #  that are in the qualBlock's register dict()
                #  these were already put into reg['registres']
                for reg, regInfo in ret['registers'].items():
                    conKey = inst+regInfo['register']
                    if conKey not in ret['connections']:
                        ret['connections'][conKey] = dict()
                    ret['connections'][conKey]['interfaceName'] = regInfo['register']
                    ret['connections'][conKey]['interface'] = regInfo['register']
                    ret['connections'][conKey]['channelName'] = regInfo['register']
                    ret['connections'][conKey]['struct'] = regInfo['structure']
                    ret['connections'][conKey]['channelCount'] = 1
                    if(regInfo['regType'] == 'ext'):
                        ret['connections'][conKey]['interfaceType'] = 'external_reg'
                    else:
                        ret['connections'][conKey]['interfaceType'] = 'status'
                    ret['connections'][conKey]['registerLeaf'] = None
                    ret['connections'][conKey]['ends'] = dict()
                    ret['connections'][conKey]['ends'][inst] = dict()
                    ret['connections'][conKey]['ends'][inst]['instance'] = self.data['instances'][inst]['instance']
                    ret['connections'][conKey]['ends'][inst]['portName'] = regInfo['register']
                    ret['connections'][conKey]['ends'][inst]['name'] = regInfo['register']
                    ret['connections'][conKey]['ends'][inst]['interfaceName'] = regInfo['register']
                    ret['connections'][conKey]['ends'][inst]['direction'] = regDirection['reg'].get(regInfo['regType'], None)
                    ret['connections'][conKey]['ends'][inst]['instanceType'] = self.data['instances'][inst]['instanceType']
                    structs[regInfo['structureKey']] = 0
                for mem, memInfo in self.data['memories'].items():
                    if memInfo['block'] == self.data['instances'][inst]['container'] and memInfo['regAccess']:
                        conKey = inst+memInfo['memory']
                        ret['connections'][conKey] = dict()
                        ret['connections'][conKey]['interfaceName'] = memInfo['memory']+'Regs'
                        ret['connections'][conKey]['interfaceType'] = 'memory'
                        ret['connections'][conKey]['registerLeaf'] = None
                        ret['connections'][conKey]['ends'] = dict()
                        ret['connections'][conKey]['ends'][inst] = dict()
                        ret['connections'][conKey]['ends'][inst]['instance'] = self.data['instances'][inst]['instance']
                        ret['connections'][conKey]['ends'][inst]['portName'] = memInfo['memory']
                        ret['connections'][conKey]['ends'][inst]['interfaceName'] = memInfo['memory']+'Regs'
                        structs[memInfo['structureKey']] = 0
                        consts[memInfo['wordLinesKey']] = 0
        channelCounter = dict()
        channelTotal = dict()
        channelDisambiguate = dict()
        # for hw use case we need to ensure the channel is unique or create an array
        # first idenify the array cases
        for conn,connVal in ret['connections'].items():
            channel = connVal['interfaceName']
            if channel in channelDisambiguate:
                # only duplicate channels will get here
                channelDisambiguate[channel] = True
                channelCounter[channel] = 0
                channelTotal[channel] += 1
            else:
                # unique channel (for now)
                channelDisambiguate[channel] = False
                channelTotal[channel] = 1
        # now we have a dict of special cases, create the names
        for conn,connVal in ret['connections'].items():
            channel = connVal['interfaceName']
            connVal['channelCount'] = channelTotal[channel]
            if channelDisambiguate[channel]:
                connVal['channelIndex'] = channelCounter[channel]
                if channelCounter[channel]==0:
                    # we want to ensure in the jinga we only declare the channel on the first encounter
                    connVal['channelDeclare'] = True
                else:
                    connVal['channelDeclare'] = False
                channelCounter[channel] += 1
            else:
                connVal['channelDeclare'] = True

        # create jinja friendly names
        for connMapKey, connMapValue in self.connectionMaps[qualBlock].items():
            if connMapValue['instanceKey'] in instances:
                ret['connectionMaps'][connMapKey] = connMapValue
                connMapValue['parentPortName'] = connMapValue['portName'] # portName in the block is already pre calculated
                connMapValue['instancePortName'] = getPortChannelName(connMapValue, 'instancePort') # on the instance side it depends on any instancePort set
                connMapValue['interfaceType'] = self.data['interfaces'][connMapValue['interfaceKey']]['interfaceType']

        # the definition of the ports is based on the superset of the connections
        # defined for the instances of the qualBlock
        # so we need to loop through and collect that superset of information
        # if a connection is to a block outside of the instances of interest then
        # we still want to capture it but its going to be commented out or shown as external
        for inst in qualBlockInstances:
            # loop through all the connections defined for this instance
            for conn, connVal in self.connections[inst].items():
                # is this connection to be considered in scope?
                if conn in self.connections['_external']:
                    inScope = False
                    # TODO make this language specific
                    commentOut = '//'
                else:
                    inScope = True
                    commentOut = ''
                # assume interface uniqueness is based on portName
                interface = connVal['interfaceKey'] + getPortChannelName(connVal)
                # add it for later iteration to calc superset
                interfaces[interface] = None

                if interface not in ports:
                    ports[interface] = dict()
                if inst not in ports[interface]:
                    ports[interface][inst] = dict()
                ports[interface][inst][conn] = connVal
                ports[interface][inst][conn]['inScope'] = inScope
                ports[interface][inst][conn]['commentOut'] = commentOut
                if connVal['_context'] == '_global':
                    # this is a generated interface
                    if connVal['interface'] == 'apb':
                        ret['addressDecode']['portName'] = connVal['portName']

        # port also may be defined by a connectionMap from parent
        # however this is not true for the top block as it has no parent so check if its in the connectionMap first
        if parentBlock in self.connectionMaps:
            # lets review all the parents connectionMaps to see if one of them is about us
            for connMapKey, connMapValue in self.connectionMaps[parentBlock].items():
                inst = connMapValue['instanceKey']
                # is this one of us?
                if inst in qualBlockInstances:
                    interface = connMapValue['interfaceKey'] + getPortChannelName(connMapValue, 'instancePort')
                    interfaces[interface] = None

                    if interface not in ports:
                        ports[interface] = dict()
                    if inst not in ports[interface]:
                        ports[interface][inst] = dict()
                    ports[interface][inst][connMapKey] = connMapValue.copy()
                    ports[interface][inst][connMapKey]['port'] = getPortChannelName(connMapValue, 'instancePort')
                    ports[interface][inst][connMapKey]['inScope'] = True
                    ports[interface][inst][connMapKey]['commentOut'] = ''

        # loop through interfaces to create the superset
        ret['ports'] = ports
        for interface in interfaces:
            count = 0
            for inst in ports[interface]:
                # how many instances of this interface are needed
                count = max(len(ports[interface][inst]), count)
                # ref for later use, will point to last one
            this = ports[interface][inst][next(iter(ports[interface][inst]))]
            portNameThis = getPortChannelName(this)
            ret['ports'][interface]['count'] = count
            ret['ports'][interface]['name'] = portNameThis
            ret['ports'][interface]['channelName'] = portNameThis
            ret['ports'][interface]['direction'] = this['direction']
            ret['ports'][interface]['port'] = this['port']
            ret['ports'][interface]['commentOut'] = this['commentOut']

            interfaceKey = this['interfaceKey']

            ret['ports'][interface]["interfaceData"] = self.data['interfaces'][interfaceKey]
            ret['ports'][interface]["connectionData"] = this
            if self.data['interfaces'][interfaceKey]['structures']:
                for structInfo in self.data['interfaces'][interfaceKey]['structures']:
                    structs[structInfo['structureKey']] = 0

        for reg, regConn in ret['registerConnections'].items():
            myReg = dict()
            myReg['name'] = regConn['register']
            myReg['commentOut'] = ''
            myReg['interfaceData'] = regConn
            regInfo = self.data['registers'][regConn['registerBlock']]
            myReg['interfaceData']['desc'] = regInfo['desc']
            myReg['interfaceData']['structures'] = list()
            myReg['interfaceData']['structures'].append({'structure': regInfo['structure'], 'structureKey': regInfo['structureKey'], 'structureType': 'data_t'})
            myReg['connectionData'] = dict()
            if regInfo['regType'] == 'ext':
                interfaceType = 'external_reg'
            else:
                interfaceType = 'status'
            myReg['direction'] = regDirection['blk'].get(regInfo['regType'], None)
            if myReg['direction'] is None:
                printError(f"Unknown register type {regInfo['regType']} for register {reg}")
                exit(warningAndErrorReport())
            myReg['interfaceData']['interfaceType'] = interfaceType
            myReg['connectionData']['direction'] = myReg['direction']
            myReg['interfaceData']['interface'] = regInfo['register']
            ret['regPorts'][reg] = myReg
            structs[regInfo['structureKey']] = 0

        # Test and if this qualBlock has a leafInstance set meaning that it is a register / apb leaf register decode block
        #   then we want to include the registers inside this block as well for generation
        if qualBlockLeafInstance and len(qualBlockInstances) == 1:
            parentBlock = self.getQualBlock(qualBlockLeafInstanceContainer)
            regPorts['ports'] = dict()
            for reg, regInfo in self.data['registers'].items():
                if regInfo['blockKey'] == parentBlock:
                    regPorts['ports'][reg] = regInfo
                    regPorts['ports'][reg]['name'] = regInfo['register']
                    regPorts['ports'][reg]['commentOut'] = ''
                    regPorts['ports'][reg]['interfaceData'] = regInfo
                    regPorts['ports'][reg]['interfaceData']['structures'] = list()
                    regPorts['ports'][reg]['interfaceData']['structures'].append({'structure': regInfo['structure'], 'structureKey': regInfo['structureKey'], 'structureType': 'data_t'})
                    regPorts['ports'][reg]['interfaceData']['connectionData'] = dict()
                    if regInfo['regType'] == 'rw':
                        regPorts['ports'][reg]['interfaceData']['interfaceType'] = 'status'
                        regPorts['ports'][reg]['direction'] = 'src'
                    elif regInfo['regType'] == 'ro':
                        regPorts['ports'][reg]['interfaceData']['interfaceType'] = 'status'
                        regPorts['ports'][reg]['direction'] = 'dst'
                    elif regInfo['regType'] == 'ext':
                        regPorts['ports'][reg]['interfaceData']['interfaceType'] = 'external_reg'
                        regPorts['ports'][reg]['direction'] = 'src'
                    else:
                        assert(0)
                    regPorts['ports'][reg]['interfaceData']['connectionData']['direction'] = regPorts['ports'][reg]['direction']
                    regPorts['ports'][reg]['interfaceData']['interface'] = regInfo['register']
                    structs[regInfo['structureKey']] = 0
            ret['ports'].update(regPorts['ports'])
            # for ease of SystemVerilog generation make a dictionary that indicates a registerLeafInstance
            #  exists and what it's container is for later processing
            ret['registerLeafInstance'] = {'container': qualBlockLeafInstanceContainer}
        elif qualBlockLeafInstance and len(qualBlockInstances) > 1:
            printError(f"Instances with registerLeafInstance set can only be instantiated once! Block = {qualBlock} instantiated more than once")
            exit(warningAndErrorReport())

        ret['addressDecode']['hasDecoder'] = addressDecoder
        if addressDecoder:
            #addressConfig = self.config.getConfig('ADDRESS_CONFIG')
            instanceInfo = self.data['instances'][next(iter(qualBlockInstances))]
            addressGroup = instanceInfo['addressGroup']
            ret['addressDecode']['addressBits'] = (addressConfig['AddressGroups'][addressGroup]['addressIncrement'] * instanceInfo['addressMultiples']).bit_length()
            ret['addressDecode']['addressGroup'] = addressGroup
            #ret['addressDecode']['decodePort'] =

        if isApbRouter or addressDecoder:
            # search for the interface definition in block ports
            ret['addressDecode']['registerBusStructs'] = dict()
            for apbIfPort in filter(lambda x: x['interfaceData']['interfaceType'] == 'apb', ret['ports'].values()):
                for item in filter(lambda x: x['interface'] == addressConfig['RegisterBusInterface'], apbIfPort['interfaceData']['structures']):
                    ret['addressDecode']['registerBusStructs'].update( { item['structureType'] : item['structure'] } )
                    ret['addressDecode']['registerBusInterface'] = addressConfig['RegisterBusInterface']
            # if we have found no register bus structs then report an error
            if not ret['addressDecode']['registerBusStructs']:
                printError(f"Register Bus Interface {addressConfig['RegisterBusInterface']} not found in ports of block {qualBlock}")
                exit(warningAndErrorReport())


        sourceContexts = self.extractContext(structs, consts)
        for sourceContext in sourceContexts:
            if sourceContext not in self.specialContexts:
                ret['includeContext'][sourceContext] = 0

        ret['hierKey'] = self.hierKey[qualBlock]
        ret['blockName'] = self.data['blocks'][qualBlock]['block']
        # get all the blocks referenced, note that as this will reduce to one entry per block type
        # hierKey contains all the instance info
        for inst, instVal in self.hierKey[qualBlock].items():
            if inst in instances:
                ret['subBlocks'][instVal['instanceTypeKey']] = instVal['instanceType']

        return ret
    # do some preproccessing to assemble subset of data easily accessed by templates
    # from perspective of qualBlock
    # subBlocks will be referenced if in the set of instances
    # this would be easier in SQL..
    def getBlockData(self, qualBlock, trimRegLeafInstance=False, excludeInstances=set()):
        blockDataSet = {'connections','memoryConnections', 'registerConnections', 'connectionMaps', 'connectionPorts', 'memoryPorts',
                        'registerPorts', 'connectionMapPorts', 'ports', 'connectDouble', 'connectSingle', 'subBlocks', 'includeContext',
                        'addressDecode', 'variants', 'interfaceTypes', 'prunedConnections', 'interface_defs', 'interface_type_mappings', 
                        'interface_type_mappings_qualified'}
        ret = dict()
        # create some of the simple returns
        ret['includeFiles'] = self.config.getConfig('INCLUDEFILES')
        ret['qualBlock'] = qualBlock
        ret['blockInfo'] = self.data['blocks'][qualBlock]
        ret['temp'] = dict()
        ret['temp']['structs'] = dict()
        ret['temp']['consts'] = dict()
        ret['temp']['registerInterfaceTypes'] = dict()
        for k in blockDataSet:
            ret[k] = dict()
        ret['addressDecode']['hasDecoder'] = False
        # assemble the instance information. This is the instances of the qualBlock and any contained instances
        self.getBDInstances(qualBlock, ret, trimRegLeafInstance, excludeInstances)
        # get all the register and memory information
        self.getBDRegistersMemories(qualBlock, ret)
        # based on memories and registers, do we need address decoding etc
        self.getBDAddressDecode(ret)
        # address bus info
        self.getBDAddressBus(ret)
        # memory connections
        self.getBDMemoryConnections(ret)
        # register connections
        if ret['enableRegConnections']:
            self.getBDRegisterConnections(ret)
            if not ret['blockInfo']['isRegHandler']:
                ret['registers'] = dict()
        # connection maps
        self.getBDConnectionMaps(ret)
        # regular connections
        self.getBDConnections(ret, allowSingleEnded=(len(excludeInstances)!=0))
        # build final connection info
        self.getBDConnectionsFinal(ret)
        # deduplicate the ports
        self.getBDPorts(ret)
        # figure out includes
        self.getBDIncludes(ret)
        # collect interface definitions for all interface types used in the block
        self.getBDInterfaceDefs(ret)
        ret.pop('temp') # remove temp data

        return ret

    def _lookupInterfaceTypeKey(self, intf_type):
        """Simple lookup for interface type qualified key when not from interfaces table        
        For types like 'memory' etc. that are constructed, not from interfaces table.
        """
        all_interface_defs = self.data.get('interface_defs', {})
        
        if intf_type in all_interface_defs:
            return intf_type
        for parent_key, mappings_dict in all_interface_defs.items():
            if mappings_dict['interface_type'] == intf_type:
                return parent_key
        return None
    
    def getBlockDataHier(self, qualBlock, trimRegLeafInstance=False, excludeInstances=set()):
        def recurse_block(block, trimRegLeafInstance, excludeInstances, visited=None):
            if visited is None:
                visited = set()
            if block in visited:
                return None  # Prevent infinite recursion on cyclic references
            visited.add(block)
            data = self.getBlockData(block, trimRegLeafInstance, excludeInstances)
            for subBlockKey in list(data['subBlocks'].keys()):
                subData = recurse_block(subBlockKey, trimRegLeafInstance, excludeInstances, visited)
                data['subBlocks'][subBlockKey] = subData
            return data
        return recurse_block(qualBlock, trimRegLeafInstance, excludeInstances)

    def getBDGetIntfStructs(self, ret, intfData={}, intfKey=''):
        if not intfData:
            intfData = self.data['interfaces'][intfKey]
        if intfData['structures']:
            for structInfo in intfData['structures']:
                ret['temp']['structs'][structInfo['structureKey']] = 0
        # Store qualified interface type key for direct lookup later
        # The parser already stores this as interfaceTypeKey after validation
        intf_type = intfData['interfaceType']
        intf_type_key = intfData.get('interfaceTypeKey', None)
        ret['interfaceTypes'][intf_type] = intf_type_key

    def getBDInstances(self, qualBlock, ret, trimRegLeafInstance, excludeInstances):
        qualBlockInstances = dict()
        containedInstances = dict()
        containerBlocks = dict()
        excluded = dict()
        hasExcluded = 0
        for inst_key, inst_data in self.data['instances'].items():
            if inst_data.get('containerKey') == qualBlock:
                if inst_data['instance'] in excludeInstances:
                    hasExcluded = 1
                    excluded[inst_key] = inst_data
                    continue
                containedInstances[inst_key] = inst_data
                if self.data['blocks'][inst_data['instanceTypeKey']]['isRegHandler']:
                    ret['regHandler'] = inst_key
            if inst_data.get('instanceTypeKey') == qualBlock:
                qualBlockInstances[inst_key] = inst_data
                containerBlocks[inst_data['containerKey']] = 0
                if inst_data['variant'] != '':
                    filtered_variants_data = {k: v for k, v in self.data['parameters'][qualBlock]['variants'].items() if v.get('variant') == inst_data['variant']}
                    ret['variants'][inst_data['variant']] = filtered_variants_data
        if len(qualBlockInstances) == 0:
            printError(f"There are no instances of {qualBlock} in the design")
            exit(warningAndErrorReport())
        ret['instances'] = qualBlockInstances
        ret['enableRegConnections'] = True
        if trimRegLeafInstance and 'regHandler' in ret:
            # if the only contained instance is the regHandler then remove it
            if (len(containedInstances) + hasExcluded) == 1:
                containedInstances = dict()
                ret['enableRegConnections'] = False
        ret['subBlockInstances'] = containedInstances
        ret['containerBlocks'] = containerBlocks
        ret['blockName'] = self.data['blocks'][qualBlock]['block']
        for inst, instInfo in containedInstances.items():
            ret['subBlocks'][instInfo['instanceTypeKey']] = instInfo['instanceType']
        if hasExcluded == 0 and len(excludeInstances) > 0:
            printError(f"--excludeInst={excludeInstances} did not find any of the instances to exclude in block {qualBlock}")
            exit(warningAndErrorReport())
        ret['excludedInstances'] = excluded

    def getBDRegistersMemories(self, qualBlock, ret):
        # figure out which memories are either in this block or accessible through registers
        block = qualBlock
        isRegHandler = ret['blockInfo']['isRegHandler']
        if isRegHandler:
            # for register handler blocks we want the registers from the parent block
            block = ret['instances'][next(iter(ret['instances']))]['containerKey'] # note there should be a 1:1 relationship for reg handler
            decodeBlock = block
            # figure out an instance of the parent block
            # we will use this to get the address group for the address decode
            for k, v in self.data['instances'].items():
                if v['instanceTypeKey'] == decodeBlock:
                    addressGroup = v['addressGroup']
                    break
        else:
            decodeBlock = qualBlock
            instanceInfo = ret['instances'][next(iter(ret['instances']))] # we only need one instance for the info as all instances must have similar config.. TODO add more checks
            addressGroup = instanceInfo['addressGroup']

        for designObject in ['registers', 'memories']:
            data = dict()
            for obj, objInfo in self.data[designObject].items():
                if objInfo['blockKey'] == block:
                    data[obj] = dict(objInfo)
                    ret['temp']['structs'][objInfo['structureKey']] = 0
                    # handle any object specific special cases
                    if (designObject == 'memories'):
                        ret['temp']['consts'][objInfo['wordLinesKey']] = 0
                        if objInfo['regAccess']:
                            ret['addressDecode']['hasDecoder'] = True # we have memories that need FW access
                        else:
                            if isRegHandler:
                                # for a regHandler we only want memories that have regAccess
                                data.pop(obj)

                    else:
                        data[obj]['bytes'] = (self.data['structures'][objInfo['structureKey']]['width'] + 7) >> 3 # round up to whole byte
                        ret['addressDecode']['hasDecoder'] = True #register = AddressDecoder
            ret[designObject] = data

        if ret['addressDecode']['hasDecoder']:
            ret['addressDecode']['addressBits'] = (self.data['blocks'][decodeBlock]['maxAddress']).bit_length()
            ret['addressDecode']['addressGroup'] = addressGroup

    def getBDAddressDecode(self, ret):
        # is this block a special apbDecode block type that performs abp bus routing
        isApbRouter = False
        addressConfig = self.config.getConfig('ADDRESS_CONFIG', True)
        # iterate through the address config and see if we were mentioned
        if addressConfig:
            for addressGroup, addressGroupData in addressConfig.get('AddressGroups', {}).items():
                decoder = addressGroupData.get('decoderInstance', None)
                if decoder is not None:
                    qualDecoder = self.getQualInstance(decoder)
                    if qualDecoder in ret['instances']:
                        instanceWithRegApb = self.config.getConfig("INSTANCES_WITH_REGAPB", failOk=True)
                        if instanceWithRegApb is None:
                            printError('No instances with register interface found in db: missing or invalid register post processing script')
                            exit(warningAndErrorReport())
                        isApbRouter = True
                        ret['addressDecode']['addressGroupData'] = addressGroupData
                        ret['addressDecode']['addressGroup'] = addressGroup
                        ret['addressDecode']['containerBlock'] = self.instanceContainer[qualDecoder]
                        ret['addressDecode']['instanceWithRegApb'] = instanceWithRegApb
        ret['addressDecode']['isApbRouter'] = isApbRouter

    # memory connections
    def getBDMemoryConnections(self, ret):
        # go through memory connections and collect if either src or dest
        qualBlock = ret['qualBlock']
        qualBlockInstances = ret['instances']
        isRegHandler = ret['blockInfo']['isRegHandler']
        containedInstances = ret['subBlockInstances']
        for memConn, val in self.data['memoryConnections'].items():
            if val['blockKey'] == qualBlock and val['instanceKey'] in containedInstances:
                # the connection is to a memory inside the target block so we will need a channel and bindings
                ret['memoryConnections'][memConn] = dict(val)
                ret['memoryConnections'][memConn]['interfaceName'] = val['memory']+'_'+val['port']
                if (val['instance'] != ''):
                    # we are connecting to an instance so lets add the instance type for the template
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    # for local mode where we are not connecting to an instance ensure we dont get a key missing error
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = ''
                ret['temp']['structs'][self.data['memories'][val['memoryBlockKey']]['structureKey']] = 0
                ret['temp']['consts'][self.data['memories'][val['memoryBlockKey']]['wordLinesKey']] = 0
            if val['instanceKey'] in qualBlockInstances:
                # we are the instance getting a memory connection so this means we have a port
                memInfo = self.data['memories'][val['memoryBlockKey']]
                ret['memoryPorts'][memConn] = dict(memInfo, **val) # merge the two dicts
                ret['memoryPorts'][memConn]['interfaceName'] = val['memory']
                ret['memoryPorts'][memConn]['direction'] = 'src'
                ret['memoryPorts'][memConn]['interfaceType'] = 'memory'
                if (val['instance'] != ''):
                    ret['memoryPorts'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    ret['memoryPorts'][memConn]['instanceTypeKey'] = ''
                ret['temp']['structs'][self.data['memories'][val['memoryBlockKey']]['structureKey']] = 0
                ret['temp']['consts'][self.data['memories'][val['memoryBlockKey']]['wordLinesKey']] = 0

        for mem, memInfo in ret['memories'].items():
            # we also need to create a port for any memory that has regAccess as the register block will need to connect to it
            if memInfo['regAccess']:
                interfaceName = memInfo['memory']+ '_reg'
                ret['temp']['structs'][memInfo['structureKey']] = 0
                if isRegHandler:
                    ret['memoryPorts'][interfaceName] = dict(memInfo)
                    ret['memoryPorts'][interfaceName]['interfaceName'] = interfaceName
                    ret['memoryPorts'][interfaceName]['direction'] = 'src'
                    ret['memoryPorts'][interfaceName]['interfaceType'] = 'memory'
                else:
                    if ret['enableRegConnections']:
                        # we also need to create a memory connection for the register block to connect to the memory
                        ret['memoryConnections'][interfaceName] = dict(memInfo)
                        ret['memoryConnections'][interfaceName]['interfaceName'] = interfaceName
                        ret['memoryConnections'][interfaceName]['instanceKey'] = ret['regHandler']
                        ret['memoryConnections'][interfaceName]['instance'] = ret['subBlockInstances'][ret['regHandler']]['instance']
                        ret['memoryConnections'][interfaceName]['instanceTypeKey'] = ret['subBlockInstances'][ret['regHandler']]['instanceType']
                        ret['memoryConnections'][interfaceName]['direction'] = 'src'
        if isRegHandler:
            ret['memoriesParent'] = ret['memories']
            ret['memories'] = dict()
        
        # Add memory interface type only once if we have any memory ports or connections
        if ret['memoryPorts'] or ret['memoryConnections']:
            ret['interfaceTypes']['memory'] = self._lookupInterfaceTypeKey('memory')

    # register connections
    regMapReg   = { 'rw': 'src', 'ro': 'dst', 'ext': 'src' } # mapping of the register type to the registerBlock port direction
    regMapBlock = { 'rw': 'dst', 'ro': 'src', 'ext': 'dst' } # mapping of the register type to the block port direction
    def getBDRegisterConnections(self, ret):
        block = ret['qualBlock']
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        isRegHandler = ret['blockInfo']['isRegHandler']
        regHandlerKey = ret.get('regHandler', None)
        regHandler = ''
        connected_regs = dict()
        if regHandlerKey:
            regHandler = self.data['instances'][regHandlerKey]['instance']
        if isRegHandler:
            # for a register handler the registerConnections are in the parent
            block = ret['instances'][next(iter(ret['instances']))]['containerKey']
        for regConn, val in self.data['registerConnections'].items():
            if val['blockKey'] == block and val['instanceKey'] in containedInstances:
                reg_name = val['register']
                connected_regs[reg_name] = 0
                regType =  ret['registers'][val['registerBlockKey']]['regType']
                ifType = 'reg_' + regType
                regInfo = ret['registers'][val['registerBlockKey']]
                ret['temp']['structs'][regInfo['structureKey']] = 0
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                if isRegHandler:
                    ret['registerPorts'][regConn] = dict(regInfo, **val)
                    ret['registerPorts'][regConn]['direction'] = self.regMapReg.get(ret['registers'][val['registerBlockKey']]['regType'], None)
                    ret['registerPorts'][regConn]['interfaceType'] = ifType
                else:
                    connKey = regInfo['register']
                    if connKey not in ret['registerConnections']:
                        output = dict(regInfo, **val)
                        inst = val['instance']
                        output['ends'] = dict()
                        output['ends'][inst] =          {'instance': inst,       'portName': reg_name, 'direction': self.regMapBlock[regType]}
                        output['ends'][regHandlerKey] = {'instance': regHandler, 'portName': reg_name, 'direction': self.regMapReg[regType]}
                        output['interfaceType'] = ifType
                        output['interfaceName'] = reg_name
                        ret['registerConnections'][connKey] = output
                    else:
                        inst = val['instance']
                        ret['registerConnections'][connKey]['ends'][inst] = {'instance': inst, 'portName': reg_name, 'direction': self.regMapBlock[regType]}
            if val['instanceKey'] in qualBlockInstances:
                portName = val['register']
                connected_regs[portName] = 0
                regInfo = self.data['registers'][val['registerBlockKey']]
                ret['registerPorts'][portName] = dict(regInfo, **val) # merge the two dicts
                regType = regInfo['regType']
                ret['registerPorts'][portName]['direction'] = self.regMapBlock.get(regType, None)
                ifType = 'reg_' + regType
                ret['registerPorts'][portName]['interfaceType'] = ifType
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                ret['temp']['structs'][regInfo['structureKey']] = 0
        # handle implied register connections. These interfaces connect any unconnected registers to the block
        implied_reg = dict()
        for reg_key, reg_data in ret['registers'].items():
            reg = reg_data['register']
            if reg not in connected_regs:
                regType = reg_data['regType']
                ifType = 'reg_' + regType
                implied_reg[reg] = dict(reg_data)
                implied_reg[reg]['interfaceType'] = ifType
                if isRegHandler:
                    implied_reg[reg]['direction'] = self.regMapReg[regType]
                else:
                    implied_reg[reg]['interfaceName'] = reg
                    implied_reg[reg]['ends'] = dict()
                    inst = next(iter(qualBlockInstances))
                    implied_reg[reg]['ends'][inst] = {'instance': qualBlockInstances[inst]['instance'], 'portName': reg, 'direction': self.regMapBlock[regType]}
                    implied_reg[reg]['ends'][regHandlerKey] = {'instance': regHandler, 'portName': reg, 'direction': self.regMapReg[regType]}
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                ret['temp']['structs'][reg_data['structureKey']] = 0
        if isRegHandler:
            ret['registerPorts'].update(implied_reg)
        else:
            ret['registerConnections'].update(implied_reg)
    # connection maps
    def getBDConnectionMaps(self, ret):
        qualBlock = ret['qualBlock']
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        for connMapKey, connMap in self.data['connectionMaps'].items():
            # note we check that a valid qualBlock connects to a contained instance in case it was pruned (regBlock)
            if connMap['blockKey'] == qualBlock and connMap['instanceKey'] in containedInstances:
                ret['connectionMaps'][connMapKey] = dict(connMap)
                ret['connectionMaps'][connMapKey]['interfaceName'] = connMap['portName']
                ret['connectionMaps'][connMapKey]['parentPortName'] = connMap['portName']
                self.getBDGetIntfStructs(ret, intfKey=connMap['interfaceKey'])
            if connMap['instanceKey'] in qualBlockInstances:
                # use portName as the key to deduplicate the port definitions
                portName = connMap['instancePortName']
                ret['connectionMapPorts'][portName] = dict(connMap)
                self.getBDGetIntfStructs(ret, intfKey=connMap['interfaceKey'])

    # regular connections
    def getBDConnections(self, ret, allowSingleEnded=False):
        # iterate through all the connections for the instances of interest
        ports = dict()
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        excludeInstances = ret['excludedInstances']
        connections = dict()
        prunedConnections = dict()
        for conn, connVal in self.data['connections'].items():
            connectionCount = 0
            isPort = False
            tempPorts = dict()
            pop_ends = []
            for end, endVal in connVal['ends'].items():
                if endVal['instanceKey'] in containedInstances:
                    connections[conn] = dict(connVal)
                    connectionCount += 1
                if endVal['instanceKey'] in qualBlockInstances:
                    isPort = True
                    tempPorts[end] = endVal
                if endVal['instanceKey'] in excludeInstances:
                    pop_ends.append(end)
                    prunedConnections[conn] = 0
            # filter out any excluded instances after looping
            for end in pop_ends:
                connVal['ends'].pop(end)
            if isPort:
                # shallow copy
                ports[conn] = dict(connVal)
                # replace ends with our pruned version
                ports[conn]['ends'] = tempPorts
            if connectionCount == 1 and not allowSingleEnded:
                printError(f"Connection {conn} is only connected to one contained instance in block {ret['qualBlock']}. Connections must be between two contained instances")
                exit(warningAndErrorReport())
            if connectionCount > 0 and isPort:
                printError(f"Connection {conn} is connected to both a contained instance and the parent instance in block {ret['qualBlock']}. Connections must be between two contained instances")
                exit(warningAndErrorReport())
            if connectionCount > 1 or isPort:
                # Get interfaceTypeKey from the interfaces table (already has qualified key)
                intfInfo = self.data['interfaces'][connVal['interfaceKey']]
                intf_type = intfInfo['interfaceType']
                ret['interfaceTypes'][intf_type] = intfInfo.get('interfaceTypeKey', None)
        for conn, connVal in connections.items():
            # create jinja friendly names
            connVal['interfaceName'] = getKeyPriority(connVal, ['interfaceName', 'srcport', 'name', 'interface'])
            intfInfo = self.data['interfaces'][connVal['interfaceKey']]
            self.getBDGetIntfStructs(ret, intfData=intfInfo)
            connVal['interfaceType'] = intfInfo['interfaceType']
            for end, endVal in connVal['ends'].items():
                endVal['name'] = endVal['portName']
        # move all the pruned connections to a separate dict
        for conn in prunedConnections:
            ret['prunedConnections'][conn] = connections.pop(conn)

        ret['connections'] = connections
        ret['connectionPorts'] = ports

    connMapping = { 'connectDouble': ['connections', 'registerConnections'],
                    'connectSingle': ['connectionMaps', 'memoryConnections'] }

    def getBDConnectionsFinal(self, ret):
        # deduplicate the channels
        duplicateCheck = dict()
        duplicateList = []
        for connType, connSources in self.connMapping.items():
            for connSource in connSources:
                ret[connType][connSource] = dict()
                for conn, connVal in ret[connSource].items():
                    channel = connVal['interfaceName']
                    index = 0
                    if channel in duplicateCheck:
                        if connVal['interfaceKey'] != duplicateCheck[channel]['connInfo']['interfaceKey']:
                            printError(f"Connection {conn} in {connSource} has the same channel name {channel} as another connection but different interface types "
                                       f"{self.data['interfaces'][connVal['interfaceKey']]['interfaceType']} and "
                                       f"{self.data['interfaces'][duplicateCheck[channel]['connInfo']['interfaceKey']]['interfaceType']}. Please rename one of the channels")
                            exit(warningAndErrorReport())
                        if connType != duplicateCheck[channel]['connType'] or connSource != duplicateCheck[channel]['connSource']:
                            printError(f"Connection {conn} in {connSource} has the same channel name {channel} as another connection but different connection types "
                                       f"{connType} and {duplicateCheck[channel]['connType']}. Please rename one of the channels")
                            exit(warningAndErrorReport())
                        count = duplicateCheck[channel]['count']
                        if count == 1:
                            duplicateList.append(channel)
                        duplicateCheck[channel]['conns'][conn] = count
                        index = count
                        duplicateCheck[channel]['count'] = count + 1
                    else:
                        duplicateCheck[channel] = {'connType': connType, 'connSource': connSource, 'connInfo': connVal, 'conns': {conn: 0}, 'count': 1}
                    ret[connType][connSource][conn] = dict(connVal)
                    ret[connType][connSource][conn]['channelCount'] = 1
                    ret[connType][connSource][conn]['index'] = index
        for channel in duplicateList:
            connType = duplicateCheck[channel]['connType']
            connSource = duplicateCheck[channel]['connSource']
            channelCount = duplicateCheck[channel]['count']
            for conn, connDisambiguate in duplicateCheck[channel]['conns'].items():
                ret[connType][connSource][conn]['channelCount'] = channelCount


    def getBDPorts(self, ret):
        # iterate through the port definitions to deduplicate
        ports = dict()
        newPorts = dict()
        for conn, connVal in ret['connectionPorts'].items():
            for end, endVal in connVal['ends'].items():
                portName = endVal['portName']
                self.getBDAddPort(ports, newPorts, portName, endVal)
                temp = dict(connVal, **ports[portName])
                temp['connection']['interfaceKey'] = connVal['interfaceKey']
                self.getBDGetIntfStructs(ret, intfKey=connVal['interfaceKey'])
                ports[portName] = temp
        ret['ports']['connections'] = dict(ports)
        portTypes = {'connectionMapPorts': {'dest': 'connectionMaps', 'portName': 'instancePortName'},
                     'registerPorts': {'dest': 'registers', 'portName': 'register'},
                     'memoryPorts': {'dest': 'memories', 'portName': 'memory'}}
        for connType, portType in portTypes.items():
            newPorts = dict()
            for conn, connVal in ret[connType].items():
                self.getBDAddPort(ports, newPorts, connVal[portType['portName']], connVal)
            ret['ports'][portType['dest']] = dict(newPorts)

    def getBDAddPort(self, ports, newPorts, portName, connVal):
        instanceKey = connVal.get('instanceKey', 'parent')
        if portName not in ports:
            ports[portName] = dict()
            ports[portName]['connection'] = dict(connVal)
            ports[portName]['instance'] = {instanceKey: 0}
            ports[portName]['name'] = portName
            ports[portName]['direction'] = connVal.get('direction', 'src') # default to src for memory case
            newPorts[portName] = dict(ports[portName])
        else:
            if instanceKey in ports[portName]['instance']:
                printError(f"Duplicate port definition found for {portName} instance {instanceKey}")
                exit(warningAndErrorReport())
            else:
                ports[portName]['instance'][instanceKey] = 0

    def getBDAddressBus(self, ret):
        if ret['addressDecode']['isApbRouter'] or ret['addressDecode']['hasDecoder']:
            # search for the interface definition
            ret['addressDecode']['registerBusStructs'] = dict()
            addressConfig = self.config.getConfig('ADDRESS_CONFIG', True)
            ret['addressDecode']['registerBusInterface'] = addressConfig['RegisterBusInterface']
            interfaceInfo = [x for x in self.data['interfaces'].values() if x.get('interface') == addressConfig['RegisterBusInterface']]
            if not interfaceInfo:
                printError(f"Register Bus Interface {addressConfig['RegisterBusInterface']} from addressConfig does not match any yaml"
                           f"defined interface definitions. This is necessary to define what interface type is used for registers")
                exit(warningAndErrorReport())
            for regIf in interfaceInfo:
                for item in regIf['structures']:
                    ret['addressDecode']['registerBusStructs'].update( { item['structureType'] : item['structure'] } )

    def getBDIncludes(self, ret):
        sourceContexts = self.extractContext(ret['temp']['structs'], ret['temp']['consts'])
        for sourceContext in sourceContexts:
            if sourceContext not in self.specialContexts:
                ret['includeContext'][sourceContext] = 0

    def getBDInterfaceDefs(self, ret):
        """Collect interface definitions for all interface types used in the block
        
        Creates a simple mapping from interface type aliases to canonical interface types.
        This allows 'reg_ro' to map to 'status', etc.
        """
        # Get interface_defs from loaded data
        all_interface_defs = self.data.get('interface_defs', {})
        
        # Build simple mapping: alias -> qualified canonical interface type
        # by filtering interface_defs that have mappedFrom data
        # Example: {'reg_ro': 'status/_a2csystem', 'reg_rw': 'control/_a2csystem', ...}
        type_mappings = {}
        type_mappings_qualified = {}
        for qual_key, intf_def in all_interface_defs.items():
            if 'mappedFrom' in intf_def and intf_def['mappedFrom']:
                for mapping_key, mapping_data in intf_def['mappedFrom'].items():
                    if 'mapped_type' in mapping_data:
                        mapped_type = mapping_data['mapped_type']
                        # Only include mappings for register interface types we're using
                        if mapped_type in ret['temp']['registerInterfaceTypes']:
                            type_mappings[mapped_type] = intf_def['interface_type']
                            type_mappings_qualified[mapped_type] = qual_key
                            ret['interfaceTypes'][intf_def['interface_type']] = qual_key
        
        ret['interface_type_mappings'] = type_mappings
        for intf_type, qual_key in ret['interfaceTypes'].items():
            ret['interface_defs'][intf_type] = all_interface_defs[qual_key]

    def extractContext(self, structs, consts):
        ret = dict()
        todo = structs
        while todo:
            nextLoop = dict()
            for structKey in todo:
                struct = self.data['structures'][structKey]
                ret[struct['_context']] = 0
                for field, fieldData in struct['vars'].items():
                    if fieldData['varTypeKey']:
                        context = fieldData['varTypeKey'].split('/', 1)[1]
                    elif fieldData['subStructKey']:
                        context = fieldData['subStructKey'].split('/', 1)[1]
                        nextLoop[fieldData['subStructKey']] = 0
                    ret[context] = 0
                    if '/' in fieldData['arraySizeKey']:
                        context = fieldData['arraySizeKey'].split('/', 1)[1]
                        ret[context] = 0
            todo = nextLoop
        for const in consts:
            if '/' in const:
                context = const.split('/', 1)[1]
                ret[context] = 0
        return ret

    # create dictionary of blocks and the connections that they contain within the scope of instances
    def setContainedConnections(self, top, instances):
        self.blockContainedConnection[self.data['instances'][top]['instanceTypeKey']] = dict()
        for instance in instances:
            self.blockContainedConnection[self.data['instances'][instance]['instanceTypeKey']] = dict()
        for conn,connVal in self.data['connections'].items():
            for end, endVal in connVal['ends'].items():
                if endVal['direction']=='src':
                    src = endVal['instanceKey']
                    srcContainer = self.data['instances'][src]['containerKey']
                else:
                    dst = endVal['instanceKey']
                    dstContainer = self.data['instances'][dst]['containerKey']
            # in context of interest?
            if src in instances and dst in instances:
                if srcContainer != dstContainer:
                    printError(f"Src {src} and dst {dst} for connection {conn} not between peers")
                    exit(warningAndErrorReport())
                self.blockContainedConnection[self.data['instances'][src]['containerKey']][conn] = connVal

    def resolveConnectionEnd(self, end, hier, nestedPort = None):
        ret = None
        # end could be initial real connection or a nested hierarchical mapping
        # try getting port used for real connection
        if nestedPort is None:
            port = end.get('portId', None)
        else:
            port = nestedPort

        this = self.data['connectionMaps'].get(port, None)
        if this:
            # this is a connection that has been mapped (if the hierarchy includes the instance within range limitations)

            # check if we even have more hierarchy to decend down
            moreHier = hier['more']
            if moreHier:
                # we have some nested hier
                nestedHier = moreHier.get(this['instanceKey'], None)
                if nestedHier:
                    if this['instancePort']:
                        nextPort = nestedHier['instanceTypeKey'] + this['instancePort']
                    else:
                        nextPort = nestedHier['instanceTypeKey'] + this['port']
                    # continue down the rabbit hole
                    ret = self.resolveConnectionEnd(this, nestedHier, nestedPort=nextPort)
        # eventually there is no more rabbit hole or no more connection maps, so get the name
        if not ret:
            ret = hier['hierarchyName']
        return ret

    def resolveConnectionEnds(self, parent, hier, connKey, connVal):
        ret = dict()
        for dir, end in connVal['ends'].items():
            # this should always be safe at the top
            subHier = hier['more'][end['instanceKey']]
            ret[end['direction']] = self.resolveConnectionEnd(end, subHier)
        return ret

    def getHierConnections(self, parent, hierInst, flatInstances):
        connections = list()
        # based on the parent instance, what is the parent block type
        parentBlock = self.data['instances'][parent]['instanceTypeKey']
        # there can only be connections if there are contained instances which might be depth limited
        if hierInst['more']:
            # get all the connections contained by parent
            if parentBlock in self.blockContainedConnection:
                for conn, connVal in self.blockContainedConnection[parentBlock].items():
                    ret =  self.resolveConnectionEnds(hierInst['hierarchyName'], hierInst, conn, connVal)
                    ret['structures'] = self.data['interfaces'][connVal['interfaceKey']]['structures']
                    ret['interface']  = self.data['interfaces'][connVal['interfaceKey']]['interface']
                    ret['desc']       = self.data['interfaces'][connVal['interfaceKey']]['desc']
                    connections.append(ret)
            # now recurse the contained instances if there are any

            for inst, subHier in hierInst['more'].items():
                ret = self.getHierConnections(inst, subHier, flatInstances)
                connections = connections + ret
        return connections

    def setRangeOfInstances(self, startInstance, depth):
        # iterativly recurse the structure. Every interation builds set of newInstances the next level down
        toProcess = [startInstance]
        for d in range(depth):
            newInstances = OrderedDict()
            for inst in toProcess:
                newInstances.update( self.getHier(inst) )

            self.rangeOfInstances.update(newInstances)
            toProcess = newInstances

    # Return a dictionary of instances
    #  each instance is a dictionary as well that contains the following keys
    #       instanceType
    #       color
    #       hierarchyName - this is a long hierarchical name in cases of larger depth
    #       more          - this dictionary if None means no more instances contained
    #                         otherwise another dictionary of instances are inside
    #
    # The result is a dictionary of instance keys in heirarchical form
    def setRangeOfInstancesByHier(self, startInstance, depth):
        newInstances = self.addHierEntry(startInstance, '')
        newInstances['more'] = self.recursiveHier(startInstance, (self.hierKey[self.data['instances'][startInstance]['instanceTypeKey']]), 0, depth)

        return newInstances

    def addHierEntry(self, inst, parentName):
        ret = dict()
        ret['instanceType']  = self.data['instances'][inst]['instanceType']
        ret['instanceTypeKey']  = self.data['instances'][inst]['instanceTypeKey']
        ret['color']         = self.data['instances'][inst]['color']
        ret['desc']          = self.data['blocks'][self.blocks[ret['instanceType']]]['desc']
        if len(parentName)>0:
            ret['hierarchyName'] = parentName+'.'+inst
        else:
            ret['hierarchyName'] = inst
        return ret

    # This is a helper furnction for setRangeOfInstancesByHier
    # This function helps build the recursive dictionary(s) while managing the depth chosen
    def recursiveHier(self, parentName, instances, currentDepth, depth):
        currentDepth = currentDepth + 1
        newInstances = dict()
        for inst in instances:
            newInstances[inst] = self.addHierEntry(inst, parentName)
            if (len(self.hierKey[self.data['instances'][inst]['instanceTypeKey']]) > 0 and currentDepth != depth):
                newInstances[inst]['more'] = self.recursiveHier(parentName+'.'+inst, (self.hierKey[self.data['instances'][inst]['instanceTypeKey']]), currentDepth, depth)
            else:
                newInstances[inst]['more'] = None

        return newInstances

    # Returns the contexts for a single block / instance
    def getContexts(self, instance):
        contexts = []
        i = self.qualInstance(instance)
        for k, v in self.yamlContext[self.data['instances'][i]['_context']].items():
            contexts.append(k)

        return (contexts)

    # if no instance list provided it will use internal rangeOfInstances
    # create the set of connection and connectionMap
    def initConnections(self, instances=None):
        if instances is None:
            instances = self.rangeOfInstances
        # create instance for connection and block for connectionMap structures from rangeOfInstances
        blocks = dict()
        for instance in instances:
            self.connections[instance] = OrderedDict()
            block = self.data['instances'][instance]['instanceTypeKey']
            blocks[block] = None
            self.connectionMaps[block] = OrderedDict()

        self.connections['_external'] = OrderedDict()
        external = dict()
        previousKey = ""
        for connKey, connection in self.data['connections'].items():
            capture = False
            # there are 4 cases
            # both src and destination are of interest
            # either source or dst are of interest (2 cases)
            # neither are of interest
            # the main problem is that when just 1 is mentioned, it can be of either order
            for dir, dirconn in connection['ends'].items():
                # is a instance of interest mentioned
                if dirconn['instanceKey'] in instances:
                    # put the merge of the two dicts into the connection map
                    self.connections[dirconn['instanceKey']][connKey] = {**dirconn, **connection}
                    # delete the ends as redundant
                    del self.connections[dirconn['instanceKey']][connKey]['ends']
                    # detect if we are on the second part of one sided capture (the not capture ensures the second part)
                    if connKey==previousKey and not capture:
                        self.connections['_external'][connKey] = external[connKey]
                    previousKey = connKey
                    capture = True
                else:
                    if capture:
                        # we are on second part of one sided capture
                        self.connections['_external'][connKey] = dirconn
                    previousKey = connKey
                    external[connKey] = dirconn
        # scan through all the connectionMaps and gather any that are for the set of blocks of interest
        # group by block
        for connMapKey, connMap in self.data['connectionMaps'].items():
            block = connMap['blockKey']
            if block in blocks:
                self.connectionMaps[block][connMapKey] = connMap

    def getHier(self, instance):
        ret = OrderedDict()
        #instance can be qualified or un qualified
        # if its an unqualified name, then convert to qualified or assume its already qualified if not found
        qualInstance = self.instances.get(instance, instance)
        if isinstance(qualInstance, dict):
            printError(f'Unqualified name provided that was not unique:"{instance}" ')
            exit(warningAndErrorReport())

        if qualInstance not in self.data['instances']:
            printError(f'Invalid instance:"{instance}" is not part of design')
            exit(warningAndErrorReport())
        block = self.data['instances'][qualInstance]['instanceTypeKey']
        return (self.hierKey[block].copy())

    def qualInstance(self, instance):
        ret = self.instances.get(instance, None)
        if ret is None:
            printError(f'Invalid instance:"{instance}" is not part of design')
            exit(warningAndErrorReport())
        return ret

    def getQualBlockVariants(self, qualBlock):
        variants = []
        variantData = self.data['parameters'].get(qualBlock, {}).get('variants', {})
        for _, data in variantData.items():
            if data['variant'] not in variants:
                variants.append(data['variant'])
        return(variants)

# this class is used to create the database based on the schema
# it also contains the logic to validate the yaml files against the schema
# it also contains the logic to validate the addressControl file
# it should be noted that the data is held in dictionarys during the parsing process
# but unlilke the user representation, it is held in context form to allow
# input to be scope checked. The context is removed during the save to the database
class projectCreate:
    proj = None
    a2cProj = None
    schemaYaml = None
    schema = None
    data = dict()
    addressControl = None
    topInstance = None
    counterGroup = OrderedDict() # for counter group current values
    counterGroupControl = OrderedDict() # for counter group control info
    counterData = OrderedDict() # record allocation of values
    counterReverseField = None
    addressObjects = OrderedDict()
    yamlAllFiles = OrderedDict()
    yamlUnread = list()
    yamlRaw = dict()
    yamlDependancies = OrderedDict()
    yamlContext = OrderedDict() #dict containing precalculated contexts by file
    const = dict() # contains constants by yamlfile scope
    qualConst = dict() # contains constants by qualified name
    enums = dict() # contains enums by yamlfile scope
    qualEnums = dict() # contains enums by qualified name
    # section are simple, custom or something inbetween.
    #simple sections dont need any special handling - no auto fields
    simpleSections = {"types", "blocks", "variables", "interfaces", "instances", 'connectionMaps', "structures", "memories", "registers", "memoryConnections", "registerConnections", "parameters" }
    #custom section require complete custom section handling including the main loop
    customSections = {"connections"}
    # any section inbetween has a per entry handler
    ignoreSections = {"include", "flows", "includeName", "blockDir" } # note all project file field are added later
    generatorTemplates = {"cppConfig", "svConfig", "docConfig" }
    dontValidate = {'_topInstance'} # list of keys that should not be validated if validator is present
    stdFields = {"context"}
    specialContexts = {"_global", "_a2csystem"} # special contexts that should be excluded from includes
    constFind = re.compile(r"(\$)(\w+)")
    currentContext = None
    errorState = False
    includeName = dict()
    includeValid = dict()
    includeSections = {"types", "structures", "constants"}
    hier = None
    hierKey = None
    instances = None
    instanceContainer = None
    blocks = None
    a2cRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #parent directory of pysrc
    yamlDir = None

    def __init__(self, projFile, dbFile):

        if os.path.exists(dbFile):
            os.remove(dbFile)

        g.db = sqlite3.connect(dbFile)
        if g.debug:
            g.db.row_factory = dict_factory
        else:
            g.db.row_factory = sqlite3.Row
        g.cur = g.db.cursor()
        #initialize the config object
        self.config = config(RO = False)
        global dirMacros
        #load project file from command line
        self.proj = existsLoad(projFile)
        # the behavour or project file settings is as follows
        # for some settings the user project setting overrides the a2c defaults - eg schema is either user defined or a2c defined
        # for other settings they may be additive, eg template mappings are additive ie you get all the a2c defaults
        # however an individual template definition can be overridden by the user
        # pro vs base is simplier, pro overrides any base settings
        if (os.path.exists(os.path.join(self.a2cRoot, "../pro"))):
            self.a2cRoot = os.path.join(self.a2cRoot, "../")
        self.a2cRoot = os.path.abspath(self.a2cRoot)
        dirMacros = { "a2c" : self.a2cRoot }
        proProj = loadIfExists( os.path.join(self.a2cRoot, "pro/config/project.yaml"))
        baseProj = loadIfExists( os.path.join(self.a2cRoot, "config/project.yaml"))
        # merge pro with base overriding base
        self.a2cProj = { **baseProj, **proProj }
        self.config.setConfig('A2CROOT', self.a2cRoot)
        self.config.setConfig('A2CPROJ', self.a2cProj)
        # save the global base path referenced by project file location
        g.yamlBasePath = os.path.dirname(os.path.abspath(projFile))
        os.chdir(os.path.dirname(os.path.abspath(projFile)))
        schemaFile = resolveFilePath(self.proj, self.a2cProj, "dbSchema", self.a2cRoot )
        # read schema file referenced by project
        self.schemaYaml = existsLoad(schemaFile)
        # initialize schema base on the schema file
        self.schema = Schema(self.schemaYaml, schemaFile)
        self.counterReverseField = self.schema.counter_reverse_field

        if self.proj.get("addressControl"):
            # load and check the addressControl file specified in the project file
            addressControlFile = self.proj["addressControl"]
            self.addressControl = existsLoad(addressControlFile)
            self.validateAddressControl(self.addressControl, addressControlFile)
        if 'topInstance' in self.proj:
            # all designs have a top instance, which must be specified in the project file
            self.topInstance = self.proj['topInstance']
        else:
            printError(f"Project file {projFile} is missing topInstance: setting.")
            exit(warningAndErrorReport())
        self.projectDirs()
        self.configTemplates()
        #anything except for specific keys in the project file are all saved to the config for later use
        # this also allows user additions to the project file to make it through to the generators
        self.createProjectConfig()
        # save the base yaml path as well incase needed by the generators
        self.config.setConfig('BASEYAMLPATH', g.yamlBasePath)
        # create all the databases based on the schema
        self.createDatabase(self.schema.data['schema'])
        # Load system files first (from a2cProj - base/pro config)
        systemFiles = []
        if "systemFiles" in self.a2cProj:
            # Use a2cRoot directly as the base path since it's already set correctly
            systemFiles = self.getFileList(self.a2cProj, self.a2cRoot)[0]
        
        # Then load user project files
        userFiles = self.getFileList(self.proj, g.yamlBasePath)[0]
        
        # Combine with system files first (so they process with priority)
        self.yamlUnread = systemFiles + userFiles
        self.systemFiles = set(systemFiles)  # Track which are system files
        #read all the files into project
        self.readRaw()
        # process all files
        self.processYamls()
        # run any user provided post processing
        self.postYamlExternalScript()
        # create database indexes
        self.generateIndexes()
        # perform all address calculations
        self.calcAddresses()
        # generate address enums and types
        self.generateAddressEnums()
        # check include files are valid
        self.saveIncludeFiles()
        # save the schema as well to the config
        self.validatePorts()
        self.schema.save()
        self.config.setConfig('YAMLCONTEXT', self.yamlContext, bin=True) # save the structure of the yaml contexts for header usages
        self.config.setConfig('INCLUDENAME', self.includeName, bin=True) # save the structure of the yaml contexts for header usages

        g.db.commit()
        g.db.close()
        printIfDebug("Process Complete")

    def projectDirs(self):
        global dirMacros
        if 'dirs' in self.proj:
            if 'root' not in self.proj['dirs']:
                self.logError("Definition for project root directory missing in project file. This should reflect the root of all generated files and is relative to project file")
            for dir in self.proj['dirs']:
                path = self.proj['dirs'][dir]
                path = expandDirMacros(path)
                dirMacros[dir] = os.path.abspath(path)
        self.config.setConfig('DIRS', dirMacros)

    def createProjectConfig(self):
        # save anything in project file to config except named items
        notConfig = {"projectFiles", "dirs", "systemFiles"}
        toSave = {'TOPINSTANCE': '_top', "PROJECTNAME": "Nameless"} #initialize to some defaults as appropriate
        for item in self.proj:
            # to allow later processing of nested project files we need to ensure the lower level parser ignores them by adding them to the set
            self.ignoreSections.add(item)
            if item not in notConfig:
                toSave[item.upper()] = self.proj[item]
        for item in toSave:
            self.config.setConfig(item, toSave[item])
        for item in self.a2cProj:
            self.ignoreSections.add(item)

    def parseTemplateFile(self, templateType, project):
        ret = dict()
        if templateType in project:
            configFile = expandDirMacros(project[templateType])
            a2cTemplates = existsLoad(configFile)
            # copy everything but the templates to return dict
            ret = {k: v for k, v in a2cTemplates.items() if k != 'templates'}
            # manually process the templates to expand any macros
            if 'templates' in a2cTemplates:
                ret['templates'] = dict()
                for template, fileName in a2cTemplates['templates'].items():
                    fileNameExpanded = expandDirMacros(fileName)
                    ret['templates'][template] = os.path.abspath(fileNameExpanded)
        return ret

    def configTemplates(self):
        templateConfig = dict()
        for templateType in self.generatorTemplates:
            templateConfig[templateType] = self.parseTemplateFile(templateType, self.a2cProj)
            # merge the user defined templates after the a2c defaults so that user can override
            userTemplates = self.parseTemplateFile(templateType, self.proj)
            templateConfig[templateType].update({k: v for k, v in userTemplates.items() if k != 'templates'})
            templateConfig[templateType]['templates'].update(userTemplates.get('templates', {}))
        self.config.setConfig('TEMPLATE_CONFIGS', templateConfig)

    def logError(self, msg):
        self.errorState = True
        printError(msg)
        if not continueOnError:
            exit(warningAndErrorReport())

    def logWarning(self, msg):
        self.errorState = False
        printWarning(msg)

    def postYamlExternalScript(self):
        if "postProcess" in self.proj:
            self.generateHierarchy()
            # create 'fake' global context to allow processing
            self.yamlContext['_global'] = {key: None for key in self.yamlContext}
            self.yamlContext['_global']['_global'] = None
            for script in self.proj["postProcess"]:
                fileName = basePathRelative(expandDirMacros(script))
                scriptCode = loadModule(fileName)
                newData = scriptCode.postProcess(self)
                if newData:
                    self.processSingleFile("_global", sections=newData)
            del self.yamlContext['_global']
        g.db.commit()

    def generateIndexes(self):
        for table in self.schema.tables:
            for index in self.schema.data['indexes'][table]:
                sql = f"CREATE INDEX idx_{table}_{index} ON {table} (\"{index}\")"
                g.cur.execute(sql)

    def createDatabase(self, schema, level=""):

        for table, cols in schema.items():
            self.createTable(level+table, cols)

    def createTable(self, table, cols):

        col = comma = ""
        for field in cols:
            if isinstance(cols[field], dict):
                self.createTable(table+field, cols[field])
            else:
                col = f"{col}{comma}\"{field}\"" # field is quoted to allow for sql reserved words
                comma = ", "
        self.schema.data['colsSQL'][table] = col
        sql = f"CREATE TABLE {table} ({col})"
        g.cur.execute(sql)
        self.data[table] = dict()

    def generateHierarchy(self):
        (hier, hierKey, qualInstances, instanceContainer, blocks) = generateHierarchy(self.data['instances'], self.data['blocks'], withContext=True)
        self.hier = hier
        self.hierKey = hierKey
        self.instances = qualInstances
        self.instanceContainer = instanceContainer
        self.blocks = blocks

    def getFileList(self, data, basePath):
        todoNorm = list()
        incNorm = list()
        if not data:
            return (todoNorm, incNorm)
        # Handle systemFiles (needs macro expansion)
        if "systemFiles" in data:
            systemF = data["systemFiles"]
            for f in systemF:
                # Expand macros like $a2c before resolving path
                expandedPath = expandDirMacros(f)
                todoNorm.append(os.path.relpath(os.path.join(basePath, expandedPath), g.yamlBasePath))
        if "projectFiles" in data:
            todo = data["projectFiles"]
            for f in todo:
                todoNorm.append(os.path.relpath(os.path.join(basePath, f), g.yamlBasePath))
        if "include" in data:
            inc = data["include"]
            for f in inc:
                incNorm.append(os.path.relpath(os.path.join(basePath, f), g.yamlBasePath))
            todoNorm.extend(incNorm)
        return(todoNorm, incNorm)

    def readRaw(self):
        # read files until nothing left to do
        while self.yamlUnread:
            newFiles = list()
            for f in self.yamlUnread:
                myBase = os.path.dirname(f)
                if f not in self.yamlAllFiles:
                    self.yamlAllFiles[f] = None
                    self.yamlRaw[f] = existsLoad(f)
                    (todo, include) = self.getFileList(self.yamlRaw[f], myBase)
                    if self.yamlRaw[f] and "includeName" in self.yamlRaw[f]:
                        self.includeName[f] = self.yamlRaw[f]["includeName"]
                    else:
                        self.includeName[f] = os.path.splitext(os.path.basename(f))[0]
                    for t in todo:
                        if t not in self.yamlAllFiles:
                            newFiles.insert(0, t)
                    if f in self.yamlDependancies:
                        self.yamlDependancies[f].update(include)
                    else:
                        self.yamlDependancies[f] = include

            self.yamlUnread = newFiles

    def calcAddresses(self):
        # maintain a dict of the next available offset in a block
        blockAddressCurrent = dict()
        # loop through address generating objects
        for addressType, addressInfo in self.addressObjects.items():
            # alignment can be a number or special key
            try:
                alignment = int(addressInfo['alignment'])
                alignmentModeValue = True
            except ValueError:
                alignmentModeValue = False
            sortDescending = addressInfo.get('sortDescending', False)
            sizeRoundUpPowerOf2 = addressInfo.get('sizeRoundUpPowerOf2', False)
            allocateOrder = dict()
            # get everything that needs an address, sorted by block type then entry order. Entry order is maintained
            # to allow engineers to keep consistency of address generation and ensure addresses only change when intended
            if addressType == 'memories':
                sql = f"select a.*, a.ROWID, s.width from {addressType} as a, structures as s where a.structureKey = s.structureKey and a.regAccess = 1 order by blockKey, a.ROWID"
            else:
                sql = f"select a.*, a.ROWID, s.width from {addressType} as a, structures as s where a.structureKey = s.structureKey order by blockKey, a.ROWID"
            g.cur.execute(sql)
            data = g.cur.fetchall()
            currentBlock = ""
            keyField = self.schema.data['key'][addressType] + 'Key' # use the context disambiguated varient of the key for the address object
            for row in data:
                # as data is sorted by block, detect when the block changes
                if row['blockKey'] != currentBlock:
                    currentBlock = row['blockKey']
                    if currentBlock not in blockAddressCurrent:
                        blockAddressCurrent[currentBlock] = 0
                if addressType == 'registers':
                    # width is in bits so convert to bytes and ensure alignment
                    #        bits to bytes              round up to alignment
                    size = ((((row['width'] + 7) >> 3 ) + alignment - 1 ) // alignment ) * alignment
                if addressType == 'memories':
                    # memories can be aligned to an alignment value or to memory sized boundaries.
                    # memory size is based on the next rounded power of 2 of the data width, due to address decoding requirements
                    size = roundup_pow2min4((row['width'] + 7) >> 3) * self.qualConstParse(row['wordLinesKey'])
                    if sizeRoundUpPowerOf2:
                        size = roundup_pow2min4(size)
                    if alignmentModeValue:
                        size = ((size + alignment - 1) // alignment ) * alignment
                allocateOrder[row[keyField]] = size
            if sortDescending:
                # sort data list in ascending order of size
                data.sort(key=lambda x: allocateOrder[x[keyField]], reverse=True)
            for row in data:
                size = allocateOrder[row[keyField]]
                currentBlock = row['blockKey']
                offset = blockAddressCurrent[currentBlock]
                if addressType == 'memories':
                    if alignmentModeValue:
                        size = ((size + alignment - 1) // alignment ) * alignment
                        offset = ((offset + alignment - 1) // alignment ) * alignment
                        blockAddressCurrent[currentBlock] = offset + size
                    else:
                        # memory size alignment simplifies HW address decode
                        offset = ((blockAddressCurrent[currentBlock] + size - 1) // size ) * size
                        blockAddressCurrent[currentBlock] = offset + size
                blockAddressCurrent[currentBlock] = offset + size
                sql = f"UPDATE {addressType} SET offset = {offset} WHERE \"{keyField}\" = '{row[keyField]}'" # field is quoted to allow for sql reserved words
                g.cur.execute(sql)

        # once all addresses are calculated we need to perform space checks
        for context in self.data['instances']:
            for instance, instData in self.data['instances'][context].items():
                # not every instance has used any space, so only check the ones that do
                if instData['instanceTypeKey'] in blockAddressCurrent:
                    # available is based on the number of size of each address space in that group * addressMultiples
                    availableSpace = self.addressControl['AddressGroups'][instData['addressGroup']]['addressIncrement'] * instData['addressMultiples']
                    if blockAddressCurrent[instData['instanceTypeKey']] > availableSpace:
                        printError(f"Block {instData['instanceKey']} overflowed its address space. Used: {blockAddressCurrent[instData['instanceTypeKey']]}. Available: {availableSpace}")
                        exit(warningAndErrorReport())
        for blockKey, address in blockAddressCurrent.items():
            sql = f"UPDATE blocks SET maxAddress = {address-1} WHERE blockKey = '{blockKey}'"
            g.cur.execute(sql)


    def generateAddressEnums(self):
        self.yamlContext['_global'] = {key: None for key in self.yamlContext}
        # calculate all the enums and types
        typesEnum = dict()
        for group in self.counterGroupControl.get('AddressGroups', []):
            # create a dictionary of all the enums and types for this group
            typesEnum[group] = {'desc': f'Generated type for addressing {group} instances',   'enum': list()}
        for context in self.data['instances']:
            for instance, instData in self.data['instances'][context].items():
                if instData.get('addressGroup', None) is not None:
                    # this block needs an address space
                    group = instData['addressGroup']
                    control = self.counterGroupControl['AddressGroups'][group]
                    typesEnum[group]['enum'].append( { 'enumName': control['enumPrefix'] + instance.upper(), 'desc': instance + ' instance address', 'value': instData['addressID']} )
        #convert the dictionary keys from group to the varType from the addressControl
        for group in typesEnum:
            dataToAdd = {'types': dict()}
            if len(typesEnum[group]['enum']) > 0:
                if 'varTypeContext' in self.counterGroupControl['AddressGroups'][group]:
                    context = self.counterGroupControl['AddressGroups'][group]['varTypeContext']
                    if context not in self.yamlContext:
                        printError(f"In address control file, AddressControl group:{group} specified varTypeContext:{context} which is not a valid context")
                        exit(warningAndErrorReport())
                else:
                    (decoder, context) = self.getFromContext('instances', '_global', self.counterGroupControl['AddressGroups'][group]['decoderInstance'], NotFoundFatal=True)
                    if decoder:
                        (decoderContainer, context) = self.getFromContext('blocks', '_global', decoder['containerKey'])
                if context:
                    dataToAdd['types'][ self.counterGroupControl['AddressGroups'][group]['varType'] ] = typesEnum[group].copy()
                    self.processSingleFile(context, sections=dataToAdd)

        # add to the table

        del self.yamlContext['_global']

    def saveIncludeFiles(self):
        files = dict()
        if 'fileGeneration' in self.proj:
            if 'fileMap' in self.proj['fileGeneration']:
                self.config.setConfig('FILEMAP', self.proj['fileGeneration']['fileMap'])
                for fileType, fileInfo in self.proj['fileGeneration']['fileMap'].items():
                    mode = fileInfo.get('mode', 'block')
                    if mode == 'context':
                        files[fileType] = fileInfo

        includeFiles = dict()
        for fileType, fileData in files.items():
            smartInclude = fileData['cond']['smartInclude']
            for include, includeData in self.includeValid.items():
                includeName = self.includeName[include]
                if not(smartInclude and not includeData['valid']):
                    fileName = expandNewModulePath(fileData, includeData['dir'], includeName, includeName, missingDirOk=True)
                    for ext in fileData['ext']:
                        fileNameExt = fileName + "." + fileData['ext'][ext]
                        baseName = os.path.basename(fileNameExt)
                        expandedType = fileType + "_" + ext
                        if not (os.path.exists(fileNameExt)):
                            printWarning(f"File {fileNameExt} does not exist. run arch2code.py with --newmodule option")
                        includeFiles.setdefault(expandedType, {})[include] = {'baseName': baseName, 'fileName': fileNameExt}

        self.config.setConfig('INCLUDEFILES', includeFiles)



    def validateAddressControl(self, addressControl, addressControlFile):
        validGen = {'AddressGroups': {'addressIncrement': None, 'maxAddressSpaces': None, 'varType': None, 'varTypeContext': None, 'enumPrefix': None, 'decoderInstance': None, 'primaryDecode': None},
                    'RegisterBusInterface' : None,
                    'InstanceGroups': {'varType': None, 'enumPrefix': None},
                    'AddressObjects': {'alignment': None, 'sizeRoundUpPowerOf2': None, 'sortDescending': None} }

        allKeys = set(validGen.keys())
        optionalKeys = { 'InstanceGroups' }
        mandatoryKeys = allKeys - optionalKeys

        # check if addressControl is a dictionary and has the correct keys
        if not isinstance(addressControl, dict) or set(addressControl.keys()).difference(allKeys):
            printError(f"Bad addressControl detected in {addressControlFile}, Valid section types are AddressGroups|RegisterBusInterface|InstanceGroups|AddressObjects")
            exit(warningAndErrorReport())
        elif not set(addressControl.keys()).issuperset(mandatoryKeys):
            printError(f"Bad addressControl detected in {addressControlFile}, Missing mandatory section types from {list(mandatoryKeys)}")
            exit(warningAndErrorReport())

        # Check for mandatory keys in address control
        if not isinstance(addressControl, dict) or not set(addressControl.keys()).issuperset(mandatoryKeys):
            printError(f"Bad addressControl detected in {addressControlFile}, keys do not match. Valid keys are {list(validGen.keys())}")
            exit(warningAndErrorReport())

        for gen in addressControl:
            if gen=='AddressGroups':
                addressMode=True
            else:
                addressMode=False
            if gen in ['AddressGroups', 'InstanceGroups']:
                # groups
                self.counterGroup[gen] = OrderedDict()
                self.counterGroupControl[gen] = OrderedDict()
                self.counterData[gen] = OrderedDict()

                for group, groupSettings in addressControl[gen].items():
                    self.counterGroup[gen][group] = 0
                    self.counterGroupControl[gen][group] = groupSettings
                    self.counterData[gen][group] = OrderedDict()
                    for setting, val in groupSettings.items():
                        if setting not in validGen[gen]:
                            myLineNumber = groupSettings.lc.line + 1
                            printError(f"Bad addressControl detected in {addressControlFile}:{myLineNumber}, section {gen}, group {group} has unknown parameter {setting}")
                            exit(warningAndErrorReport())
            elif gen == 'RegisterBusInterface':
                self.registerBusInterface = addressControl[gen]
                # register bus interface
                if not self.registerBusInterface:
                    printError(f"Bad RegisterBusInterface detected in {addressControlFile}, section {gen} is null")
                    exit(warningAndErrorReport())
            else:
                # addressObjects
                self.addressObjects = addressControl[gen]
                for addressObject, objectSettings in self.addressObjects.items():
                    for setting, val in objectSettings.items():
                        if setting not in validGen[gen]:
                            myLineNumber = objectSettings.lc.line + 1
                            printError(f"Bad addressControl detected in {addressControlFile}:{myLineNumber}, section {gen}, group {group} has unknown parameter {setting}")
                            exit(warningAndErrorReport())
        self.config.setConfig("ADDRESS_CONFIG", addressControl, bin=True)

    def validatePorts(self):
        pass
        # todo

    def processYamls(self):
        # main outer loop for processing
        # to avoid recusion maintain dicts of processed and toProcess
        processed = dict()
        toProcess = self.yamlDependancies.copy() # initialize with the dependencies
        nextProcess = dict()
        # we need to detect circular dependencies. We do this by detecting if we did any work
        didWork = False

        # we loop through everything that needs to be processed, and process anything that has all its dependencies met
        while toProcess:
            didWork = False
            for myYaml, dep in toProcess.items():
                if not dep:
                    # if there are no dependancies, its always safe to process
                    if myYaml in self.systemFiles:
                        # System files go into special _a2csystem context
                        if '_a2csystem' not in self.yamlContext:
                            self.yamlContext['_a2csystem'] = OrderedDict()
                        self.yamlContext['_a2csystem'][myYaml] = None
                        self.processSingleFile(myYaml, contextOverride='_a2csystem')
                    else:
                        self.yamlContext[myYaml] = OrderedDict({myYaml: None})
                        self.processSingleFile(myYaml)
                    processed[myYaml] = None
                    didWork = True
                else:
                    # we have dependencies, need to check if all dependancies are satisfied
                    allDep = True
                    # loop through all the dependencies
                    for f in dep:
                        if f not in processed:
                            # an unmet dependancy, so put this item into the do over list
                            nextProcess[myYaml] = dep
                            allDep = False
                            # no need for additional dependency checks
                            break
                        else:
                            #maybe should delete met dependancies...
                            if myYaml not in self.yamlContext:
                                # add the file itself to its own context
                                self.yamlContext[myYaml] = OrderedDict({myYaml: None})
                            self.yamlContext[myYaml][f] = None
                            # if performance of this is slow, we might want to fix later
                            self.yamlContext[myYaml].update(OrderedDict.fromkeys(self.yamlDependancies[f], None))
                    # exited the loop because everything is checked or we found an unmet dependency
                    if allDep:
                        # yay
                        self.processSingleFile(myYaml)
                        processed[myYaml] = None
                        didWork = True
            toProcess = nextProcess.copy()
            nextProcess = dict()
            if toProcess and not didWork:
                printWarning("Files to process")
                printWarning(toProcess)
                printWarning("files not processed")
                printWarning(processed)
                printError("Circular include dependancy detected")
                exit(warningAndErrorReport())
            if self.errorState:
                exit(warningAndErrorReport())
        g.db.commit()

    # process a single previously read file or provided standalone data
    def processSingleFile(self, yamlFile, sections=None, contextOverride=None):
        # loop through the sections and process the section
        if sections is None:
            printIfDebug(f"Processing yaml file {yamlFile}")
            sections = self.yamlRaw[yamlFile]
        # Use contextOverride if provided (for system files in _a2csystem context)
        contextFile = contextOverride if contextOverride else yamlFile
        self.currentContext = contextFile
        if not sections:
            return
        if "blockDir" in sections:
            self.yamlDir = sections["blockDir"]
        else:
            self.yamlDir = os.path.dirname(yamlFile)
        if yamlFile not in self.includeValid and yamlFile not in self.specialContexts:
            # check if this is a nested project file
            if 'addressControl' not in sections:
                self.includeValid[yamlFile] = {"dir": self.yamlDir, "valid": False}
        # we are going to go through every section of the input yaml file and process it
        for section, sectData in sections.items():
            if section in self.schema.data['mapto']:
                section = self.schema.data['mapto'][section]
            # some sections need to be ignored (eg in case this is a nested project file)
            if section not in self.ignoreSections:
                if (section in self.schema.data['schema']):
                    # does this section have a custom section handler
                    if section in self.customSections:
                        funct = '_process_'+ section
                        # getattr is used to call the function specified in the string funct in the self object
                        getattr(self, funct)(sectData, contextFile)
                    else:
                        self.processSection(section, sectData, contextFile)
                else:
                    printError(f"Unknown section: {section} found in {yamlFile}:{sectData.lc.line}")
                    exit(warningAndErrorReport())
                if section in self.includeSections:
                    self.includeValid[yamlFile]["valid"] = True

    # loop through section handling all items for simple and inbetween sections
    def processSection(self, section, data, yamlFile):
        # print(f'Processing section {section} in {yamlFile}:{data.lc.line}')
        # create the context specific data holder for this section
        # during data parsing all data is held in context form to allow dependency checking
        if yamlFile not in self.data[section]:
            self.data[section][yamlFile] = OrderedDict()
        # some sections manage data using a combo key made up of other fields
        comboKey = self.schema.data['comboKey'].get(section, None)
        if comboKey:
            comboKeyName = self.schema.data['key'][section]
        if section == 'constants' and yamlFile not in self.const:
            # for constants initialise the lookup dict for resolution of constants
            self.const[yamlFile] = OrderedDict()
        # data input can be lists or dicts in the yaml
        isList = isinstance(data, list)
        if section == 'parameters':
            pass
        # for a given section, loop through all the items and process each item
        # note that this can be dict or list
        for loopitem in data:
            if comboKey is None:
                if isList:
                    # for list case the key is one of the data items
                    itemkey = loopitem[self.schema.data['key'][section]]
                else:
                    # for dict its the anchor of the data items ie loopitem
                    itemkey = loopitem
            else:
                # comboKey can only be handled later after other fields have been parsed
                itemkey = "" # will be filled out during parsing

            if isList:
                item = loopitem
            else:
                item = data[loopitem]
            if yamlFile in self.specialContexts:
                yamlFileOverride = item.get('_yamlFileOverride', yamlFile)
                if yamlFileOverride not in self.data[section]:
                    self.data[section][yamlFileOverride] = OrderedDict()
            else:
                yamlFileOverride = yamlFile
            if section in self.simpleSections:
                # for named simple sections that just contain simple items, go ahead and process
                entry = self.processSimple(section, itemkey, item, yamlFileOverride)
            else:
                #special sections are handled by appropriate class methods
                funct = '_'+ section
                # getattr is used to call the function specified in the string funct in the self object
                try:
                    entry = getattr(self, funct)(itemkey, item, yamlFileOverride)
                except AttributeError:
                    entry = self.processSimple(section, itemkey, item, yamlFileOverride)
                    self.simpleSections.add(section) # for user specific sections outside of default program supplied sections
            if comboKey is not None:
                # ok we have a combo key, so we can finally resolve it
                itemkey = entry[comboKeyName]
            # save everything
            self.data[section][yamlFileOverride][itemkey] = entry
            self.addRecord(section, yamlFileOverride, itemkey, entry, self.schema.data['schema'][section])

    # process a single entry and handle all the trivial cases
    # schema can be provided for sub table use cases
    # note that auto fields are ignored
    def processSimple(self, section, anchor, item, yamlFile, schema = None, context='', outer = None):
        ret = dict()
        if 'lc' in item:
            myLineNumber = item['lc'].line + 1
            ret['lc'] = item['lc']
        elif hasattr(item, 'lc'):
            myLineNumber = item.lc.line + 1
            ret['lc'] = item.lc
        else:
            myLineNumber = None
        comboKey = self.schema.data['comboKey'].get(context+section, None)
        comboSchema = self.schema.data['comboField'].get(context+section, {})
        if not schema:
            # default schema for non nested uses
            schema = self.schema.get_section(section).get_fields_dict() if self.schema.get_section(section) else {}
        
        # handle singular case and convert item to a dict
        if not isinstance(item, dict):
            if context+section in self.schema.data['singular']:
                item = {self.schema.data['singular'][context+section]: item}

        if outer == None:
            # loop through the fields in the item to make sure they are all in the schema
            for field in item:
                if not isinstance(field, dict) and not isinstance(item[field], dict):
                    if field not in schema and field not in ['eval', 'lc', '_yamlFileOverride']:
                        printWarning(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} has unknown field {field}")

        # loop through the schema processing the input one field at a time
        for field, ftype in schema.items():
            comboField = comboSchema.get(field, None)
            if isinstance(ftype, dict):
                #if ftype is a dict, snap off the whole relevant piece as a dict depending on whether required or not
                attrib = self.schema.data['attrib'][context+section+field]
                if 'collapsed' in attrib:
                    # we have a nested entry, but as its collapsed its not actually anchored in the yaml with an varname, the anchor is the actual key
                    nested = item
                else:
                    nested = item.get(field)
                if not nested and 'required' in attrib:
                    self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} required sub table {field} is missing")
                if nested:
                    if not isinstance(nested, (dict, list)):
                        printError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} required sub table {field} is missing definition")
                        exit(warningAndErrorReport())
                    # recursively process the sub entry
                    ret[field] = self.processSubTable(field, nested, yamlFile, ftype, anchor, context+section, ret)
                continue
            if ftype == 'ignore':
                # while unknown ftypes are ignored anyway, prefer to be explicit in ignoring ignore ftype
                continue
            if comboField:
                # field is created by concatenation of other fields. schema will have enforced ordering to after other fields
                # Use precomputed qualified sources from schema validation
                node = self.schema.get_node(context+section)
                field_obj = node.get_field(field) if node else None
                if not (field_obj and field_obj.combo_sources_qualified):
                    raise RuntimeError(f"Schema validation incomplete: combo field '{field}' in section '{context+section}' missing qualified sources")
                qualified_sources = field_obj.combo_sources_qualified
                comboStr = ""
                for source_field in qualified_sources:
                    if source_field not in ret or ret[source_field] is None:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, field:{field} is missing required combo source {source_field}")
                        exit(warningAndErrorReport())
                    comboStr = comboStr + ret[source_field]
                ret[field] = comboStr
                # Immediately populate the qualified field if it exists in schema
                qualified_field = field + 'Key'
                if qualified_field in schema and qualified_field not in ret:
                    ret[qualified_field] = comboStr + '/' + yamlFile

            if ftype == 'key':
                if comboKey:
                    # key is created by concatenation of other fields. schema will have enforced ordering to after other fields
                    # Use precomputed qualified sources from schema validation
                    node = self.schema.get_node(context+section)
                    if not (node and node.combo_key_sources_qualified):
                        raise RuntimeError(f"Schema validation incomplete: combo key in section '{context+section}' missing qualified sources")
                    qualified_sources = node.combo_key_sources_qualified
                    keyStr = ""
                    for source_field in qualified_sources:
                        if source_field not in ret or ret[source_field] == None:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {source_field}")
                            exit(warningAndErrorReport())
                        keyStr = keyStr + ret[source_field]
                    ret[field] = keyStr
                elif anchor:
                    # if anchor was supplied then use it
                    ret[field] = anchor
                elif field not in item:
                    # anchor was not supplied and field not in item - this is an error
                    self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} is missing required field {field}")
                else:
                    # anchor was not supplied but field is in item - use the item value
                    ret[field] = item.get(field)
                
                # Immediately populate the qualified key field if it exists in schema
                qualified_field = field + 'Key'
                if qualified_field in schema and qualified_field not in ret and field in ret:
                    ret[qualified_field] = ret[field] + '/' + yamlFile
            else:
                if ftype == 'listkey':
                    # For singleEntryList, the list item value is passed as anchor, not in item dict
                    ret[field] = anchor
                    
                    # Immediately populate the qualified key field if it exists in schema
                    qualified_field = field + 'Key'
                    if qualified_field in schema and qualified_field not in ret and field in ret:
                        ret[qualified_field] = ret[field] + '/' + yamlFile
                if ftype == 'contextKey':
                    # contextKey fields are automatically populated when their corresponding
                    # key/anchor/listkey field is processed (see immediate population after each type)
                    # If not already populated, this is a bug that needs investigation
                    if field not in ret:
                        base_field = field[:-3] if field.endswith('Key') else field
                        base_ftype = schema.get(base_field, 'unknown')
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {context}{section}, contextKey field '{field}' was not pre-populated by its base field '{base_field}' (type={base_ftype}). This is a bug in processYaml.")
                        exit(warningAndErrorReport())
                    # else: correctly pre-populated, no action needed
                if ftype == 'anchor':
                    # anchor: field value comes from YAML anchor, not from item data
                    # Used for collapsed tables where the key is the YAML structure, not a field
                    # For list tables with natural keys, anchor may be None - get value from item
                    if anchor is not None:
                        ret[field] = anchor
                    elif field in item:
                        # List table with natural key - get the key value from item data
                        ret[field] = item[field]
                    
                    # Immediately populate the qualified key field if it exists in schema
                    qualified_field = field + 'Key'
                    if qualified_field in schema and qualified_field not in ret and field in ret:
                        ret[qualified_field] = ret[field] + '/' + yamlFile
                if ftype in {'required', 'subkey'}:
                    if field not in item:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} is missing required field {field}")
                    ret[field] = item.get(field)
                if ftype in {'optional', 'optionalConst'}:
                    # note that its only optional in the input - hence get usage
                    default = self.schema.data['optionalDefault'].get(context+section+field, "")
                    ret[field] = item.get(field, default)
                if ftype=='outerkey' or ftype=='outerkeyKey' or ftype=='outer':
                    # outer key is for the nested case, we want to refer back to the entry we are nested within
                    ret[field] = outer[field]
                if ftype in {'const', 'optionalConst', 'param'}:
                    constType = ftype
                    if ftype=='param':
                        # param: field is required and can be either a block parameter or a constant
                        # parameters are instance specific so the design element must belong to a block
                        if field not in item:
                            # param field missing - this is an error (param is like required)
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {field}")
                            constType = 'const'  # Continue processing as const to avoid additional errors
                        elif 'blockKey' in ret and self.checkIsParam(ret['blockKey'], item[field], yamlFile):
                            # TODO: move this logic to an auto function
                            # Value is a block parameter - use it directly
                            ret[field] = item[field]
                        else:
                            # Value is not a parameter (or blockKey not yet available) - treat as constant
                            constType = 'const'
                    # const can be a number or a reference to a constant that has already been declared
                    itemKeyField = None
                    if constType == 'const':
                        # const is not optional so report error if missing
                        if field not in item:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {field}")
                        else:
                            ret[field], itemKeyField = self.constParse(item[field], yamlFile, value=False)
                    if constType == 'optionalConst':
                        # optionalConst is optional so only lookup if its there
                        if field in item:
                            # note we look up ret[field] here as the optional aspect is already handled above
                            ret[field], itemKeyField = self.constParse(ret[field], yamlFile, value=False)
                    # at this point we may or may not have found a const
                    if itemKeyField is not None:
                        # if constParse finds a named constant - save this value in the key field
                        ret[field+'Key'] = itemKeyField
                    else:
                        ret[field+'Key'] = ""
                if ftype=='eval':
                    # value is either provided from eval statement or a named field if present
                    if field in item:
                        # named field is present, so use that
                        ret[field] = item[field]
                    elif 'eval' in item:
                        # no named field, use eval
                        self.currentContext = yamlFile
                        # look for $XXX and if found search within context to replace symbol
                        myVal = self.constFind.sub(self.re_constReplace, item['eval'])
                        # Execute the user-provided expression with proper error handling
                        try:
                            ret[field] = eval(myVal, {}, {})
                        except Exception as e:
                            # User's eval expression failed - provide clear error
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} "
                                        f"eval expression failed: '{item['eval']}' "
                                        f"(after substitution: '{myVal}'). "
                                        f"Error: {type(e).__name__}: {str(e)}")
                            ret[field] = 0  # Set default to avoid cascading errors
                    else:
                        # Neither field nor eval provided - this is an error
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} must provide either '{field}' field or 'eval' expression")
                if ftype[:4]=='auto':
                    # auto fields are used to handle all the special cases and prevent processSimple becoming bloated
                    # hopefully this eases maintainance and makes adding new special cases simplier
                    # call the special case:
                    myAutoRet = getattr(self, self.schema.data['fnStr'][context+section+field])(section, anchor, item, field, yamlFile, ret)
                    # the special cases can create signle return field or multiple - detect and handle
                    if isinstance(myAutoRet, dict):
                        # our auto function returned multiple keys so add them all
                        ret.update(myAutoRet)
                    else:
                        # just a single field
                        ret[field] = myAutoRet
            validator = self.schema.data['validator'].get(context+section+field, None)
            if ftype=='optional' and ret[field]=="":
                #if it was an optional field and there is no value, skip validation
                validator = None
                # still need to add key field
                if field+'Key' in schema:
                    ret[field+'Key'] = ""
            if validator:
                # if we have a validator, we need to check if the value is valid in this context
                if 'values' in validator:
                    # the validator can be a simple list of valid options
                    if ret[field] not in validator['values']:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} field {field}, {item[field]} is not in the allowed values, check schema for valid valued")
                else:
                    # more complex validation necessary
                    # however we do have to avoid some special cases (for example _topInstance) which will by definition fail validation
                    if ret[field] not in self.dontValidate:
                        # search for appropriate value within the yaml context allowed for this file
                        scope = validator.get('scope', yamlFile) # if the schema specified a scope override - use that
                        (varInfo, varContext) = self.getFromContext(validator['section'], scope, ret[field], NotFoundFatal=False)
                        # if its valid then use it
                        if varInfo:
                            # as its valid we also need to capture the context key - ie what file did the referenced value come from
                            ret[field+'Key'] = ret[field] + '/' + varContext
                        else:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} field {field}, value {ret[field]} was not valid in context {scope}")
                            # add anyway to prevent key error later
                            ret[field+'Key'] = 'InvalidValueInYaml'
                    else:
                        # if this is a special value that should not be validated
                        ret[field+'Key'] = ret[field] + '/' + yamlFile
        if context+section in self.schema.data['post']:
            # if there is a post process function for this section, call it now
            funct = self.schema.data['post'][context+section]
            # getattr is used to call the function specified in the string funct in the self object
            ret = getattr(self, funct)(anchor, ret, yamlFile)
        
        return ret

    def varWidth(self, varInfo, yamlFile):
        if varInfo['entryType']=='NamedStruct':
            (structInfo, structContext) = self.getFromContext('structures', yamlFile, varInfo['subStruct'], NotFoundFatal=True)
            try:
                arraySize = int(varInfo['arraySize'])
            except ValueError:
                # otherwise lookup the constant based on the key version
                arraySize = self.qualConstParse(varInfo['arraySizeKey'])
            width = structInfo['width'] * arraySize if arraySize else structInfo['width']
        elif varInfo['entryType']=='Reserved':
            width = varInfo['align']
        else:
            (typeInfo, typeContext) = self.getFromContext('types', yamlFile, varInfo['varType'], NotFoundFatal=True)
            typeWidth = self.qualConstParse(typeInfo['width'])
            try:
                arraySize = int(varInfo['arraySize'])
            except ValueError:
                # otherwise lookup the constant based on the key version
                arraySize = self.qualConstParse(varInfo['arraySizeKey'])
            width = typeWidth * arraySize if arraySize else typeWidth
        return width

    # AUTO SECTIONS begin here
    #
    #constants: constant: key, value: eval, desc: required
    def _constants(self, itemkey, item, yamlFile):
        ret = self.processSimple('constants', itemkey, item, yamlFile)
        # constants require special section handling as we want to save the const's in dict to allow later
        if 'value' not in ret:
            self.logError(f"Processing constants in {yamlFile}:{ret['lc'].line + 1} and constant:{itemkey} does not have a 'value' or 'eval' field")
        self.const[yamlFile][itemkey] = ret['value']
        self.qualConst[itemkey+'/'+yamlFile] = ret['value']
        return ret

    def _post_add_enum(self, itemkey, item, yamlFile):
        if 'enumName' in item:
            if item['enumName'] in self.enums.get(yamlFile, {}):
                self.logError(f"Processing enums in {yamlFile}:{item['lc'].line + 1} and enum:{itemkey} has duplicate enumName {item['enumName']}")
                exit(warningAndErrorReport())
            # Defensive check - value should have been validated in processSimple (eval field type)
            # If value is missing here, validation failed earlier
            if 'value' not in item:
                # This shouldn't happen if processSimple validation works correctly
                return item  # Skip adding incomplete enum
            if yamlFile not in self.enums:
                self.enums[yamlFile] = dict()
            self.enums[yamlFile][item['enumName']] = {'value': item['value'], 'type': item['type']}
            self.qualEnums[item['enumName']+'/'+yamlFile] = {'value': item['value'], 'type': item['type']}
        return item

    def _post_validate_interface_structures(self, itemkey, item, yamlFile):
        """Validate that structureType values match parameters defined in interface_defs
        
        This performs bidirectional validation:
        1. Each structureType must be a valid parameter in interface_defs
        2. All struct-type parameters from interface_defs must be present
        """
        # Only validate if interface has interfaceType
        if 'interfaceType' not in item:
            return item
        
        intf_type = item['interfaceType']
        
        # Get the interface_defs for this interfaceType
        # Use yamlFile as context to allow user-defined interfaces, with _a2csystem as fallback
        (intf_def, intf_context) = self.getFromContext('interface_defs', yamlFile, intf_type, NotFoundFatal=False)
        
        if not intf_def:
            # If interface_defs not found, the interfaceType validation will catch this
            return item
        
        # Extract valid parameter names from interface_defs
        if 'parameters' not in intf_def:
            # No parameters defined, so no structure types are expected
            if item.get('structures'):
                line_num = item['lc'].line + 1 if hasattr(item, 'lc') else '?'
                self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}' "
                            f"has structures defined, but interface_defs '{intf_type}' does not define any parameters")
            return item
        
        # Get all valid structure types and required struct parameters
        all_params = intf_def['parameters']
        valid_structure_types = set(all_params.keys())
        
        # Filter to only struct-type parameters (these are the ones that need structures defined)
        required_struct_params = {
            param_name for param_name, param_info in all_params.items()
            if param_info.get('datatype') == 'struct'
        }
        
        # Get the structureTypes that are defined in the interface
        defined_structure_types = set()
        structures = item.get('structures', {})
        
        # Validation 1: Check each defined structureType is valid
        for struct_key, struct_data in structures.items():
            if 'structureType' not in struct_data:
                continue  # This will be caught by required field validation
            
            structure_type = struct_data['structureType']
            defined_structure_types.add(structure_type)
            
            if structure_type not in valid_structure_types:
                line_num = struct_data['lc'].line + 1 if hasattr(struct_data, 'lc') else '?'
                valid_types_str = "', '".join(sorted(valid_structure_types))
                self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}': "
                            f"structureType '{structure_type}' is not valid. "
                            f"Valid structureTypes for '{intf_type}' are: '{valid_types_str}'")
        
        # Validation 2: Check all required struct parameters are present
        missing_params = required_struct_params - defined_structure_types
        if missing_params:
            line_num = item['lc'].line + 1 if hasattr(item, 'lc') else '?'
            missing_params_str = "', '".join(sorted(missing_params))
            self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}': "
                        f"missing required structureType(s): '{missing_params_str}'. "
                        f"All struct-type parameters from interface_defs must have corresponding structures.")
        
        return item

    #interfaces: interface: key, interfaceType: required, desc: required, structname: subkey,  structureType: auto,
    def _interfaces(self, itemkey, item, yamlFile):
        # handle simple stuff first
        ret = self.processSimple('interfaces', itemkey, item, yamlFile)
        #self.addRecord('interfaces', yamlFile, itemkey, ret, self.schema['interfaces'])
        # handle nested
        intfSchema = self.schema.data['interfaces']['structures']
        attrib = self.schema.data['attrib'].get('interfacesstructures')
        subItems = ret['structures'].copy()
        if ('required' in attrib) and (not subItems):
            self.logError(f"Processing interfaces in {yamlFile} and interface:{itemkey} does not have any structures to define the interface")

        ret['structures'] = OrderedDict()
        for subkey, subItem in subItems.items():
            ret['structures'][subkey] = self.processSimple('interfaces', subkey, subItem, yamlFile, schema=intfSchema)
            #self.addRecord('interfacesstructures', yamlFile, itemkey, ret, self.schema['interfacesstructures'])
        return ret

    def _specialStructures(self, itemkey, item, yamlFile):
        ret = self.processSimple('specialStructures', itemkey, item, yamlFile)
        (varInfo, varContext) = self.getFromContext('structures', yamlFile, ret['baseStruct'], NotFoundFatal=False)
        if not varInfo:
            self.logError(f"Processing specialStructures in {yamlFile} and entry:{itemkey} does not reference valid baseStruct")
            exit(warningAndErrorReport())

        varschema = self.schema.get_node('structuresvars').get_fields_dict() if self.schema.get_node('structuresvars') else {}
        newStruct = OrderedDict()
        newStructVars = OrderedDict()
        reserved = 0
        for k, v in varInfo.items():
            if k == 'structure':
                v = ret['structure']
            if k == 'structureKey':
                v = ret['structureKey']
            if k != 'vars':
                newStruct[k] = v

        # now handle alignment
        bitpos = 0
        for var, varData in varInfo['vars'].items():
            # convert 0 to 1
            align = max(int(varData['align']), 1)
            # from the alignment calculate the correctly aligned position by rounding up to next aligned spot
            newBitpos = ((bitpos + align - 1) // align) * align
            if newBitpos != bitpos:
                # we are not naturally aligned so we need to add a reserved field for padding
                varName = 'reserved'+str(reserved)
                reserved = reserved + 1
                newItem = {
                    'structure':    ret['structure'],
                    'variable':     varName,
                    'entryType':    'Reserved',
                    'desc':         'Reserved Field for padding',
                    'align':        newBitpos-bitpos
                }
                # use process simple here to reduce maintenance if more fields added to schema
                newVar = self.processSimple("vars", varName, newItem, yamlFile, schema = varschema, context="structures", outer=newStruct)
                bitpos = newBitpos
                newStructVars[varName] = newVar
            newStructVars[var] = varData
            bitpos = bitpos + self.varWidth(varData, yamlFile)
        newStruct['vars'] = newStructVars
        newStruct['width'] = bitpos
        # add our newly constructed struct to the tables and db
        self.data["structures"][yamlFile][itemkey] = newStruct
        self.addRecord("structures", yamlFile, itemkey, newStruct, self.schema.data['schema']["structures"])
        return ret

    def _encoders(self, itemkey, item, yamlFile):
        # process the data entry piece
        ret = self.processSimple('encoders', itemkey, item, yamlFile)
        # handle enum defaults
        if ret['enumType']=="":
            ret['enumType'] = itemkey+"TypeT"
        if ret['enumPrefix'] == "":
            ret['enumPrefix'] = itemkey.upper()+"_TYPE_"
        #(varInfo, varContext) = self.getFromContext('types', yamlFile, ret['encoderType'], NotFoundFatal=True)
        encoderType = ret['encoderType']
        newEncoderType = OrderedDict()
        newEncoderType['desc'] = ret['encoderTypeDesc']
        newEncoderType['width'] = ret['encoderTypeWidth']
        encoderTypeBits = self.constParse(newEncoderType['width'], yamlFile, value=True)
        # split off the items for further processing and later adding back in
        encoderItems = ret['items']
        ret['items'] = OrderedDict()

        # sort keys in decending size based on numBits
        numBits = dict() # store the lookups
        for item in encoderItems:
            numBits[item] = self.constParse(encoderItems[item]['numBits'], yamlFile, value=True)

        sortedItemKeys = sorted(encoderItems, key=lambda x: (numBits[x]), reverse=True)
        startValue = 0
        itemOrder = 0
        inverter = 0
        if not ret['zeroBased']:
            inverter = (1 << encoderTypeBits) - 1
        for item in sortedItemKeys:
            #copy the item over. note that as we care about the order we are copying the source items one at a time
            ret['items'][item] = encoderItems[item]
            ret['items'][item]['itemOrder'] = itemOrder
            itemOrder = itemOrder + 1
            # encodingValue are the bits above the field based on the number of bits in the field
            # note that we dont know how many bits in total the encoder needs just yet
            ret['items'][item]['encodingValue'] = (startValue ^ inverter) & ~((1 << numBits[item]) - 1)
            startValue = startValue + (1 << numBits[item])
        if startValue > (1 << encoderTypeBits):
            self.logError(f"Processing encoders in {yamlFile} and encoder:{itemkey} need more bits than the encoder type:{ret['encoderType']} can hold")
            exit(warningAndErrorReport())
        ret['totalBits'] = encoderTypeBits
        ret['encodeMax'] = startValue-1
        # generate new type to hold the enum and optional constants
        # iterate through the items to generate dictionary to allow the type to be generated
        newType = OrderedDict()
        newType['enum'] = list()
        newConstants = OrderedDict()
        addConstants = False
        baseConstPrefix = ret['baseConstPrefix']
        if baseConstPrefix != "":
            addConstants = True
        if ret['enumDesc'] == "":
            newType['desc'] = f"Type of {itemkey} (auto generated from encoder section)"
        else:
            newType['desc'] = ret['enumDesc']

        for item in sortedItemKeys:
            thisEnum = OrderedDict()
            # add the type
            thisEnum['enumName'] = ret['enumPrefix']+item.upper()
            thisEnum['desc'] = ret['items'][item]['desc']
            thisEnum['value'] = ret['items'][item]['itemOrder']
            newType['enum'].append(thisEnum)
            if addConstants:
                newConstants[baseConstPrefix+item.upper()] = {'value': ret['items'][item]['encodingValue'], 'desc': 'base value for ' + ret['items'][item]['desc'] }
        if not ret['zeroBased'] and ret['extendedRangeItem'] != "":
            thisEnum = OrderedDict()
            # add the type
            thisEnum['enumName'] = ret['enumPrefix']+ret['extendedRangeItem'].upper()
            thisEnum['desc'] = ret['extendedRangeDesc']
            thisEnum['value'] = itemOrder
            newType['enum'].append(thisEnum)
        newSections = {'types': {ret['enumType']: newType, encoderType: newEncoderType}}
        if addConstants:
            newSections['constants'] = newConstants
        self.processSingleFile(yamlFile, newSections)
        #newTypeProcessed = self.processSimple('types', ret['enumType'], newType, yamlFile)
        #self.data["types"][yamlFile][ret['enumType']] = newTypeProcessed
        #self.addRecord("types", yamlFile, ret['enumType'], newTypeProcessed, self.schema.data['schema']["types"])



        return ret

    # algorithm for special portname convention
    def _auto_portName(self, section, itemkey, item, field, yamlFile, processed):
        return(getPortChannelName(item))

    # algorithm for special portname convention
    def _auto_instancePortName(self, section, itemkey, item, field, yamlFile, processed):
        return(getPortChannelName(item, "instancePort"))

    # handle structure auto sensing of type
    def _auto_entryType(self, section, itemkey, item, field, yamlFile, processed):
        subStruct = item.get("subStruct", "")
        varType = item.get("varType", "")
        entryType = item.get("entryType", "")
        if entryType == "Reserved":
            return "Reserved"
        # need to figure out what has been specified
        if subStruct:
            ret = "NamedStruct"
        elif varType:
            ret = "NamedType"
        else:
            # for named var we have to perform the validation as its outside the capabilities of simple section
            (varInfo, varContext) = self.getFromContext('variables', yamlFile, itemkey, NotFoundFatal=False)
            if not varInfo:
                #it was neither
                self.logError(f"reference {itemkey} in structure does not reference a valid variable definition in this context {yamlFile}:{item.lc.line + 1}")

            ret = { 'varType': varInfo.get('type'),
                    'varTypeKey': varInfo.get('typeKey'),
                    'desc' : varInfo.get('desc'),
                    'entryType': "NamedVar",
                    'lc' : varInfo.get('lc')}
        return ret


    # handle special case where the top block does not have a container
    def _auto_container(self, section, itemkey, item, field, yamlFile, processed):
        ret = item[field]
        # if the instance matches the defined top instance override the container
        # the override allows for nested projects
        if itemkey == self.topInstance:
            ret = "_topInstance"
        return ret

    def _auto_addressGroup(self, section, itemkey, item, field, yamlFile, processed):
        ret=item.get(field, None)
        if ret:
            if ret not in self.counterGroup.get('AddressGroups', {}):
                self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' referenced a non existant address group {ret}"
                              ", check addressGroup match your AddressControl file")
        return ret

    def _auto_addressID(self, section, itemkey, item, field, yamlFile, processed):
        #note that even if specified in instances section, will be overridden
        addressControlFields = {'addressGroup': None, 'addressID': None, 'addressMultiples': None, 'instanceGroup': None, 'instanceID': None}
        ret = None
        if processed[self.counterReverseField[section+'addressGroup']] is not None:
            group = processed[self.counterReverseField[section+'addressGroup']]
            counter = self.counterGroup['AddressGroups'][group]
            base = counter * self.addressControl['AddressGroups'][group]['addressIncrement']
            ret = {
                field: counter,
                'offset': base
            }
            self.counterGroup['AddressGroups'][group] = counter + processed[self.counterReverseField[section+'addressMultiples']]
            if self.counterGroup['AddressGroups'][group] > self.addressControl['AddressGroups'][group]['maxAddressSpaces']:
                self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' we ran out of address space, check your maxAddressSpaces: in AddressControl file")
        return ret

    def _auto_instanceGroup(self, section, itemkey, item, field, yamlFile, processed):
         # this field needs to be one of the valid InstanceGroups defined in the addressControl file
        ret=item.get(field, None)
        if not ret:
            # if not specified, use the default group
            ret = 'default'
        if ret not in self.counterGroup.get('InstanceGroups', {}):
            self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' referenced a non existant instance group {ret}")
        return ret

    def _auto_instanceID(self, section, itemkey, item, field, yamlFile, processed):
          #note that even if specified in instances section, will be overridde
        if not self.counterGroup.get(section+'InstanceGroups', None):
            group = 'default'
            if not 'InstanceGroups' in self.counterGroup:
                self.counterGroup['InstanceGroups'] = dict()
            self.counterGroup['InstanceGroups'][group] = 0
        else:
            group = item[self.counterReverseField[section+'instanceGroup']]
        ret = self.counterGroup['InstanceGroups'][group]
        self.counterGroup['InstanceGroups'][group] = ret + 1
        return ret

    # def _auto_registerLeafInstance(self, section, itemkey, item, field, yamlFile, processed):
    #     # registerLeafInstance is not enabled by default.
    #     ret = item.get(field, None)
    #     return ret

    def _auto_addressMultiples(self, section, itemkey, item, field, yamlFile, processed):
          #note that even if specified in instances section, will be overridde
        ret=item.get(field, 1)
        return ret

    def _auto_width(self, section, itemkey, item, field, yamlFile, processed):
        # width can be a number, a constant, or calculated from enum size
        userWidth = item.get(field, None)
        enum = processed.get('enum', None)
        if enum and (userWidth is None):
            valMax = 1
            for val, valItem in enum.items():
                if 'value' not in valItem:
                    printError(f"Error: Missing 'value' field in {section}:{itemkey} in {yamlFile}:{processed['lc'].line}")
                    exit(warningAndErrorReport())
                valActual = self.constParse(valItem['value'], yamlFile, value=True)
                valMax = max(valMax, valActual)
            ret = (valMax).bit_length()
        else:
            if field not in item:
                printError(f"Error: Missing {field} field in {section}:{itemkey} in {yamlFile}:{processed['lc'].line}")
                exit(warningAndErrorReport())
            ret, retContext = self.constParse(item[field], yamlFile, value=False)
            if retContext is not None:
                # constParse determined the value was a named constant. So lets use the context version
                ret = retContext
        return ret

    def _auto_structWidth(self, section, itemkey, item, field, yamlFile, processed):
        width = 0
        for var, varinfo in processed['vars'].items():
            width = width + self.varWidth(varinfo, yamlFile)
        return (width)

    def _auto_blockDir(self, section, itemkey, item, field, yamlFile, processed):
        # check if user provided an override
        ret = item.get(field, None)
        if ret:
            return ret
        return self.yamlDir

    # connections: connection: key, instance: auto, direction: auto, port: optional, connCount: optional
    # this is a complete custom handler, as the key is derived from other fields
    def _process_connections(self, data, yamlFile):

        self.data['connections'][yamlFile]=dict()
        self.data['connectionsends'][yamlFile] = dict()
        # loop through the items in the section
        for item in data:

            dirContext = dict()
            # use process simple with the data schema to extract the info and validate
            row = self.processSimple('connections_dataSchema', 'dummy', item, yamlFile, schema=self.schema.data['dataSchema']['connections'] )
            # the base entry is based on this processing
            entry = row.copy()
            # every connection has a nested table with the source and destination of the connection saved in the ends field
            entry['ends'] = dict()
            myKey = row['connection']
            # if a name is provided use that as the channel name, otherwise use the src port naming
            if row['name'] != '':
                entry['channel'] = row['name']
            else:
                entry['channel'] = ''
            for dir in ['src', 'dst']:
                (instInfo, instContext) = self.getFromContext('instances', yamlFile, row[dir], NotFoundFatal=True)
                row['instanceType'] = instInfo['instanceType']
                row['instanceTypeKey'] = instInfo['instanceTypeKey']
                row['instance'] = row[dir]
                row['instanceKey'] = row[dir+'Key']
                row['port'] = row[dir+'port']
                row['direction'] = dir
                portName = getPortChannelName(row, dir+'port') # use naming convention
                row['portName'] = portName
                if 'lc' in instInfo:
                    row['lc'] = instInfo['lc']
                elif hasattr(instInfo, 'lc'):
                    row['lc'] = instInfo.lc
                else:
                    myConnection = instInfo['instance']
                    print(f"Warning: no line number in connections section for {yamlFile}:{myConnection}")

                # the channel is declared based on the src port
                if entry['channel'] == '' and dir=='src':
                    entry['channel'] = portName
                
                endRow = self.processSimple('ends', 'dummy', row, yamlFile, schema=self.schema.data['schema']['connections']['ends'],context='connections', outer = row )

                entry['ends'][endRow['portId']]=endRow
                self.data['connectionsends'][yamlFile][endRow['portId']]=endRow


            self.addRecord('connections', yamlFile, myKey, entry, self.schema.data['schema']['connections'])


            self.data['connections'][yamlFile][myKey] = entry

        return

    def re_constReplace(self, myStr):
        return(str(self.constParse(myStr.group(2), self.currentContext, value=True)))

    # parse a constant and based on context. Return the value or the symbol based on value flag
    def constParse(self, data, context, value=True):
        found = False
        try:
            #see if its already a number
            ret = int(data)
            retContext = None
            found = True
        except: ValueError
        if not found:
            # now check from dependancies
            for myContext in self.yamlContext[context]:
                const_val = self.const.get(myContext, {}).get(data)
                if const_val is None:
                    const_val = self.enums.get(myContext, {}).get(data, {}).get('value')
                if const_val is not None:
                    ret = const_val
                    retContext = data+'/'+myContext
                    found = True
                    break
        if found:
            if value:
                return ret
            else:
                return data, retContext
        else:
            self.logError(f"Constant {data} in file {context} is unresolved")
            return 0

    def checkIsParam(self, block, param, context):
        (varInfo, varContext) = self.getFromContext('blocks', context, block, NotFoundFatal=False)
        if varInfo:
            if 'params' in varInfo:
                return param in varInfo['params']

        return False

    def qualConstParse(self, data):
        found = False
        try:
            ret = int(data)
            found = True
        except: ValueError
        if not found:
            ret = self.qualConst.get(data)
            if ret is None:
                ret = self.qualEnums.get(data, {}).get('value')
        return(ret)

    # in conversions involving context there are two main cases
    # 1. A qualified name is not specified in the key and so context range is searched for a match
    # 2. A qualified name is provided we just need to verify that the context is valid
    def getFromContext(self, objType, context, key, NotFoundFatal=True):
        ret = None
        found = False
        if '/' in key:
            # we have a qualified name so we just need to verify that the context is valid
            subKey, qualification = key.split('/', 1)
            # for global context just make sure its valid
            if context == 'global':
                # global context is always valid, just check the reference is ok
                try:
                    ret = self.data[objType][qualification][subKey]
                    found = True
                except: KeyError
            else:
                # non global context means we need to ensure that the qualification is valid for this context
                if qualification in self.yamlContext[context]:
                    try:
                        ret = self.data[objType][qualification][subKey]
                        found = True
                    except: KeyError

        # note that in case there was a slash in the name try the regular context search anyway
        if not found:
            if context == 'global':
                testVal = None
                foundContext = None
                # search all contexts for a match, flag duplicates as an error
                for qualification in self.data[objType]:
                    try:
                        testVal = self.data[objType][qualification][key]
                        if found:
                            printError(f"Duplicate key {key} found in global context during validation of {objType}")
                        found = True
                        foundContext = qualification
                    except: KeyError
                ret = testVal
                qualification = foundContext
            else:
                # loop through possible qualifications to find a match
                for qualification in self.yamlContext[context]:
                    try:
                        ret = self.data[objType][qualification][key]
                        found = True
                        break
                    except: KeyError
                
                # If not found in regular context, also search _a2csystem context
                if not found and '_a2csystem' in self.yamlContext:
                    # System files are all stored under '_a2csystem' qualification
                    try:
                        ret = self.data[objType]['_a2csystem'][key]
                        qualification = '_a2csystem'
                        found = True
                    except: KeyError

        if (not found) and NotFoundFatal:
            printError(f"{objType} {key} in file {context} is unresolved")
            exit(warningAndErrorReport())
        if not found:
            qualification = None

        return (ret, qualification)

    def processSubTable(self, section, nested, yamlFile, nestedSchema, outerItemKey, context, outer = None):
        # we have a nested table so we need to process the inner table
        # there is probably an opportunitiy for some refactoring here with ProcessSection
        ret = dict()
        nestedContext = context+section
        if nestedContext == 'memoriesports':
            pass
        if yamlFile not in self.data[nestedContext]:
            self.data[nestedContext][yamlFile] = OrderedDict()
        attribs = self.schema.data['attrib'].get(nestedContext, {})
        comboKey = self.schema.data['comboKey'].get(nestedContext, None)
        
        if 'list' in attribs:
            # if nested is a list of dictionaries then we will enumerate and process, however if it just a single enty, then it is just a key on its own
            if isinstance(nested[0], (dict, list)):
                # All list tables now have explicit keys defined in schema
                # The key value comes from item data, not from YAML anchor
                node = self.schema.get_node(nestedContext)
                
                for index, item in enumerate(nested):
                    # No anchor provided - key will come from item data
                    anchor = None
                    
                    processed = self.processSimple(section, anchor, item, yamlFile, schema=nestedSchema, context=context, outer=outer)
                    
                    # Get the key from the processed item's key field
                    key_field = node.storage_key_field if node else None
                    if not key_field:
                        self.logError(f"In file {yamlFile}, section {context}{section}, list table schema has no storage_key_field defined. This is a schema validation bug.")
                        exit(warningAndErrorReport())
                    if key_field not in processed:
                        self.logError(f"In file {yamlFile}, section {context}{section}, list table key field '{key_field}' not found in processed item. This is a processing bug.")
                        exit(warningAndErrorReport())
                    itemkey = processed[key_field]
                    
                    ret[itemkey] = processed
                    self.data[nestedContext][yamlFile][itemkey] = processed
            else:
                # Simple list of scalar values for singleEntryList
                for item in nested:
                    itemkey = item
                    ret[itemkey] = self.processSimple(section, itemkey, {}, yamlFile, schema=nestedSchema, context=context, outer=outer)
                    self.data[nestedContext][yamlFile][itemkey] = ret[itemkey]
        
        elif 'singleEntryList' in attribs:
            # Handle singleEntryList separately - items from a list become individual records
            for item in nested:
                itemkey = item
                ret[itemkey] = self.processSimple(section, itemkey, {}, yamlFile, schema=nestedSchema, context=context, outer=outer)
                self.data[nestedContext][yamlFile][itemkey] = ret[itemkey]

        else:
            if isinstance(nested, list):
                if comboKey:
                    itemkeyName = self.schema.data['key'][nestedContext]
                    itemkey = ""
                    for item in nested:
                        listret = self.processSimple(section, itemkey, item, yamlFile, schema=nestedSchema, context=context, outer=outer)
                        ret[listret[itemkeyName]] = listret
                        self.data[nestedContext][yamlFile][listret[itemkeyName]] = listret
                else:
                    printError(f"{yamlFile}:{nested.lc.line+1} {nested} unexpected in list format in file {context} this is either a schema or file error")
                    exit(warningAndErrorReport())

            else:
                if 'dataGroup' in attribs:
                    ret = self.processSimple(section, outerItemKey, nested, yamlFile, schema=nestedSchema, context=context, outer=outer)
                else:
                    for itemkey, item in nested.items():
                        ret[itemkey] = self.processSimple(section, itemkey, item, yamlFile, schema=nestedSchema, context=context, outer=outer)
                        self.data[nestedContext][yamlFile][itemkey] = ret[itemkey]
        return ret

    # add an item to the database
    def addRecord(self, table, yamlFile, itemkey, entry, schema, outerEntry=None):
        myLineNumber = 0
        if self.schema.data['multiEntry'][table]:
            # for this case we want to iterate over the items
            loop = entry
        else:
            # there is only one item, so pretend its a single entry multi item to allow looping
            loop = {itemkey: entry}
        for myEntryKey, myEntry in loop.items():
            if 'lc' in myEntry:
                myLineNumber = myEntry['lc'].line + 1
            comma = ''
            values = ''
            valueList = list()
            params = ''
            for col in schema:
                value = None
                # detect inner table
                if isinstance(schema[col], dict):
                    if col in myEntry:
                        self.addRecord(table+col, yamlFile, itemkey, myEntry[col], schema[col], outerEntry=entry)
                    continue
                if schema[col] == 'key':
                    value = myEntry.get(col, myEntryKey)
                if schema[col] in ['outerkey', 'outerkeyKey', 'outer']:
                    value = myEntry.get(col, outerEntry.get(col, None))
                    if value is None:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {table}, key:{itemkey} is missing required field {col}")
                if schema[col] == 'context':
                    value = yamlFile
                if value is None:
                    value = myEntry[col]
                    if value is None:
                        value = ''
                valueList.append(value)
                params = f"{params}{comma} ? "
                comma = ', '

            sql = f"INSERT INTO {table} ({self.schema.data['colsSQL'][table]}) values ({params})"
            # use parameterized sql to finally fix the damn appostrophe
            try:
                g.cur.execute(sql, valueList)
            except sqlite3.InterfaceError as e:
                print(f"ERROR inserting into {table}:")
                print(f"  SQL: {sql}")
                print(f"  Values: {valueList}")
                print(f"  Value types: {[type(v) for v in valueList]}")
                raise








