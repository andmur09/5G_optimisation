from topology_class import *

def make_graph(_service, _topology):
    # Makes a graph (instance of topology) representing the service
    layers = _topology.getLocationsByTypes()
    no_components = len(_service.components)
    graph_segments = {}

    for k in range(no_components+1):
        if k == 0:
            new_nodes = []
            new_edges = []
            # For the initial layer representing gateway to component1
            # Makes a copy of all nodes in all layers
            for layer in layers:
                for node in layer:
                    new_nodes.append(node.copy())
            # Makes a copy of all links in the topology
            for edge in _topology.links:    
                for source in new_nodes:
                    for sink in new_nodes:
                        if edge.source.description == source.description and edge.sink.description == sink.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
            graph_segments[str(k)] = (new_nodes, new_edges)

        elif k == no_components:
            new_nodes = []
            new_edges = []
            # For the final layer representing last component to gateway
            for layer in layers:
                for node in layer:
                    new_nodes.append(node.copy())
            for edge in _topology.links:
                for source in new_nodes:
                    for sink in new_nodes:
                        if edge.source.description == sink.description and edge.sink.description == source.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
            graph_segments[str(k)] = (new_nodes, new_edges)

        else:
            # For inter component layers:
            new_nodes = []
            new_edges = []

            out_nodes = []
            in_nodes = []
            mid_nodes = []

            intermediate_layers = layers[2:]
            for layer in intermediate_layers:
                for node in layer:
                    # Out are those for transport from component one, up the layers
                    out_nodes.append(node.copy())
                    # In nodes are from the top layer down to component two
                    in_nodes.append(node.copy())

            for node in layers[1]:
                # mid nodes are nodes in top layer (one down from gateway)
                mid_nodes.append(node)

            for edge in _topology.links:
                # Adds links between mid layers
                for source in out_nodes:
                    for sink in out_nodes:
                        if edge.source.description == sink.description and edge.sink.description == source.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
                for source in in_nodes:
                    for sink in in_nodes:
                        if edge.source.description == source.description and edge.sink.description == sink.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
                # Adds links between out layer and mid
                for source in out_nodes:
                    for sink in mid_nodes:
                        if edge.source.description == sink.description and edge.sink.description == source.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
                # # Adds links between mid layer and in
                for source in mid_nodes:
                    for sink in in_nodes:
                        if edge.source.description == source.description and edge.sink.description == sink.description:
                            new_edge = edge.copy_with_new_nodes(source, sink)
                            new_edge.setLinkCost(1)
                            new_edges.append(new_edge)
                            if edge.two_way == True:
                                new_edge = edge.copy_with_new_nodes(sink, source)
                                new_edge.setLinkCost(1)
                                new_edges.append(new_edge)
            # Adds links between out version of node and in version of same node to prevent having to go up a layer
            for source in out_nodes:
                for sink in in_nodes:
                    if source.description == sink.description:
                        new_edges.append(link(source, sink, {"bandwidth": inf, "latency": 0, "cost": 0}, two_way=False))
            new_nodes = out_nodes + mid_nodes + in_nodes

            graph_segments[str(k)] = (new_nodes, new_edges)

    # # Joins segments of graph with nodes representing assignment of component to node.
    for i in range(no_components):
        new_nodes = []
        new_edges = []
        for l in _topology.locations:
            # Adds dummy nodes representing node_component[i]
            if l.type == "node":
                new_nodes.append(location(l.description + "_" + _service.components[i].description, "dummy"))
     
        # Joins pre layer to nodes
        pre_layer = graph_segments[str(i)]
        for source in pre_layer[0]:
            for sink in new_nodes:
                # Last part checks that there is no incoming edges to the source node
                #if sink.description == source.description + "_" + _service.components[i].description:
                if sink.description == source.description + "_" + _service.components[i].description and not [l for l in pre_layer[1] if l.source == source]:
                    new_edges.append(link(source, sink, {"bandwidth": inf, "latency": 0, "cost": 0}, two_way=False))
            
        # # Joins post layer to nodes
        post_layer = graph_segments[str(i+1)]
        for source in new_nodes:
            for sink in post_layer[0]:
                # Last part checks that there is no outgoing edges to the sink node
                if source.description == sink.description + "_" + _service.components[i].description and not [l for l in post_layer[1] if l.sink == sink]:
                #if sink.description == source.description + "_" + _service.components[i].description and not [l for l in post_layer[1] if l.sink == sink]:
                    new_edges.append(link(source, sink, {"bandwidth": inf, "latency": 0, "cost": 0}, two_way=False))
            
        graph_segments["Component {}".format(i)] = (new_nodes, new_edges)
        
    nodes = []
    edges = []
    for key in graph_segments:
        nodes += graph_segments[key][0]
        edges += graph_segments[key][1]     
    return (nodes, edges)