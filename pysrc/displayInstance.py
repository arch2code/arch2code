from operator import sub
import pysrc.arch2codeGlobals as globals
from graphviz import Digraph

# This function draws a diagram of instances starting with instanceTop and drawing to a depth indicated
# by the input depth.

#   TODO change label of edges (interface lines) to strcut based on user's optional command line input
#   TODO figure out how to get the subgraphs to show a tooltip, they are cluster_ so it should work but the library may not
#          differentiate between subgraph and cluster_, tooltip currently shows cluster_'hierarchyName' with version
#          5.0.0 of graphviz, and graphviz python library 0.20
#   TODO add diagram title maybe projectName + Instance + depth
def displayInstancesDiagram(prj, instanceTop, depth, noConnections):
    # Get the top instance, set the range of instances by depth and get a flat dictionary
    # of those instance. This flat dictionary will be used to search connectionEnds later
    # for edge connection (lines on graph)
    top = prj.getQualTop(instanceTop)
    prj.setRangeOfInstances(top, depth)
    flatInstancesDictionary = prj.rangeOfInstances

    instancesDictionary = prj.setRangeOfInstancesByHier(top, depth)
    prj.setContainedConnections(top, flatInstancesDictionary)
    connectionList = prj.getHierConnections(top, instancesDictionary, flatInstancesDictionary)
    dot = Digraph(comment='Instances Diagram', node_attr={'shape': 'rect'}, graph_attr={'bgcolor': globals.bgcolor, 'tooltip': '{} + depth {}'.format(top, depth)})

    # draw nodes / blocks and if a block has blocks inside of it recurse and draw subgraphs
    #   until no more blocks insde
    for k, v in instancesDictionary['more'].items():
        if (v['more'] is None):
            label = v['instanceType']
            k = v['hierarchyName'] # rename k to the entire hierarchy path before usage
            color, style = getInstancesColorAndStyle(v)
            dot.node('{}'.format(k), label='{}'.format(label), fillcolor='{}'.format(color), style='{}'.format(style), tooltip='{}'.format(v['desc']))
        else:
            # block with blocks inside, treat it as a subgraph and recurse to draw blocks
            #   within it
            dot.subgraph(getSubGraph(prj, k, v))
    if (noConnections is False): # skip edges / interface lines is instructed via command line options
        for v in connectionList:
            # connectionsList is used to draw src / dst pairs and these pairs are already
            #   unique for instanceTop and depth chosen
            interfaceStructures = v['structures']
            toolTip = v['interface'] + '(' + getStructureNames(interfaceStructures) + ')' + ' ' + v['desc']
            dot.edge(tail_name='{}'.format(v['src']), head_name='{}'.format(v['dst']), tooltip='{}'.format(toolTip))

    # only show preveiw when the debug option is selected
    if (globals.deleteGV):
        # creates an output svg image in the specified directory
        dot.render(filename=globals.filename, directory=globals.gvdir, view=globals.debug, cleanup=globals.deleteGV, format='svg')
    else:
        # creates an output dot file with .gv and from it generates an .gv.svg image in the same directory
        dot.render(filename=globals.filename+'.gv', directory=globals.gvdir, view=globals.debug, format='svg')

# This function is a recursive subgraph drawing function for the function displayInstancesDiagram
# takes an open project, key and value
# the key is an instance's hierachical name, and value is a dictionary
# of one or more instances inside the instace described by key
def getSubGraph(prj, key, value):
    label = value['instanceType']
    key = value['hierarchyName'] # rename key to the entire hierarchy path before usage
    color, style = getInstancesColorAndStyle(value, True)
    desc = prj.data['blocks'][prj.blocks[label]]['desc']
    subGraph = Digraph('cluster_{}'.format(key), '{} subgraph'.format(key), graph_attr={'label': '{}'.format(label), 'style': '{}'.format(style), 'color': '{}'.format(color), 'tooltip': '{}'.format(desc)})
    # give the subGraph an invisible node to reference, this allows interfaces to be drawn if no subnodes exist
    #  in graphviz terms an invisible node is made to reference later just in case edges attach to it on one side
    subGraph.node('{}'.format(key), label='{}'.format(label), style='invis')
    for k, v in value['more'].items(): #then do same as calling function above
        if (v['more'] is None):
            label = v['instanceType']
            k = v['hierarchyName'] # rename k to the entire hierarchy path before usage
            color, style = getInstancesColorAndStyle(v)
            subGraph.node('{}'.format(k), label='{}'.format(label), fillcolor='{}'.format(color), style='{}'.format(style), tooltip='{}'.format(v['desc']))
        else:
            subGraph.subgraph(getSubGraph(prj, k, v))

    return subGraph


# This function is given a dictionary of an instance that contains properties about that instace,
#  specific properties are color, returns two strings for graphviz drawings that contain
#  first color and secont style
def getInstancesColorAndStyle(inDictionary, subGraph=None):
    if (inDictionary['color'] != ''):
        # return color and filled style
        return inDictionary['color'], 'filled'
    elif (subGraph):
        # Since subGraphs / clusters have slightly different attributes to nodes this returns
        # blank if no color was defined, otherwise 'white', 'filled' will be assigned with no
        # border to the subgraph, '', '' defaults to the bgcolor defined for the graph and
        # default black text and black border
        return '', ''
    else:
        # return default color and defualt style
        #   graphviz default color is lightgrey and style is ''
        #   using a document friendly version so embbeded blocks don't change the color of non color'd blocks
        return 'white', 'filled'

# This function returns a string of structures that are attached to an interface,
#   a dictionary of interfaces is the input
def getStructureNames(inDictionary):
    string = ''
    if inDictionary is None:
        return ""
    for item in inDictionary:
        string += item['structure']+', '

    string = string[:-2] # removes the last ', ' from the string of structures for this interface
    return string
