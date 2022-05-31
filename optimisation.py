import sys
import gurobipy as gp
from gurobipy import GRB
from math import sqrt, log
import numpy as np
from topology_class import location, link, topology
from service_class import service, service_graph, service_path
import graphviz as gvz

def masterProblem(topology, services):
    m = gp.Model(topology.name)
    nodes = topology.getLocationsByType("node")
    n_services = len(services)
    n_nodes = len(nodes)

    components = set()
    # Adds flow vector for each service where each element represents a path associated with that service
    # Also makes set of components for all service so that no duplicate components are considered
    for service in services:
        graph = service.graphs[topology.name]
        m.addMVar(shape=len(graph.getPaths()), vtype=GRB.CONTINUOUS, name= service.description + "_flows")
        for component in service.components:
            components.add(component)
    components = list(components)

    # Adds binary variables vector where each elemnt takes a value of 1 if the component is assigned to a particular node or 0 otherwise
    for component in components:
        m.addMVar(shape=len(n_nodes), vtype=GRB.BINARY, name=component.description + "_assignment")

    # # Adds constraint that the sum of flows for each service must be greater than the required throughput for the service
    for service in services:
        flows = m.getVarByName(service.description + "_flows")
        m.addConstr(gp.quicksum(flows) >= service.required_throughput)

    # Adds a constraint that says that the sum of all flows through the edge must be less than the bandwidth:
    for link in topology.links:
        # updated
        m.addConstr(gp.quicksum([]) >= service.required_throughput)

    # Adds a constraint that says that a component must be assigned to x different nodes where x is the replica count
    for component in components:
        assignments = m.getVarByName(component.description + "_assignment")
        m.addConstr(gp.quicksum(assignments) == component.replica_count)

    # Adds a constraint that says that the sum of component requirements running on a node must not exceed the capacity.


    # Gets number of time a link is traversed for each path
    

def columnGeneration(topology, service):
    m = gp.Model(topology.name + "_" + service.description)
    graph = service.graphs[topology.name]

    # Adds variables representing whether an edge has been used in a path or not:
    links = m.addMVar(shape=len(graph.links), vtype=GRB.BINARY, name="links")
    weights = np.array([l.cost for l in graph.links])

    # Gets indexes of links corresponding to ones leaving the source
    start = graph.getStartNode()
    outgoing = graph.outgoingEdge(start)
    start_indexes = [i for i in range(len(graph.links)) if graph.links[i] in outgoing]
    # Adds constraint that exactly one link leaving the source must be active
    m.addConstr(gp.quicksum([links[i] for i in start_indexes]) == 1)

    # Gets indexes of links corresponding to ones entering the sink
    end = graph.getEndNode()
    incoming = graph.incomingEdge(end)
    end_indexes = [i for i in range(len(graph.links)) if graph.links[i] in incoming]
    # Adds constraint that exactly one link entering the sink must be active
    m.addConstr(gp.quicksum([links[i] for i in end_indexes]) == 1)

    # Adds constraint that the sum of the flow into and out of every other edge must be conserved
    source_and_sink = [graph.locations.index(i) for i in [start, end]]
    for i in range(len(graph.locations)):
        if i not in source_and_sink:
            incoming = graph.incomingEdge(graph.locations[i])
            incoming_i = [i for i in range(len(graph.links)) if graph.links[i] in incoming]
            outgoing = graph.outgoingEdge(graph.locations[i])
            outgoing_i = [i for i in range(len(graph.links)) if graph.links[i] in outgoing]
            m.addConstr(gp.quicksum([links[i] for i in incoming_i]) == gp.quicksum([links[o] for o in outgoing_i]))
    
    m.setObjective(weights @ links, GRB.MINIMIZE)
    m.update()
    m.optimize()

    if m.status == GRB.OPTIMAL:
        print('\n objective: ', m.objVal)
        print('\n Vars:')
        for v in m.getVars():
            print("Variable {}: ".format(v.varName) + str(v.x))
    else:
        m.computeIIS()
        m.write("{}.ilp".format(m.ModelName))
        m.write("{}.lp".format(m.ModelName))
        m.write("{}.mps".format(m.ModelName))

    # From solution gets set of links
    links_i = [i for i in range(len(graph.links)) if links[i].x == 1]
    used_links = [graph.links[i] for i in range(len(graph.links)) if i in links_i]
    
    # From links gets set of nodes and adds path
    used_nodes = set()
    for link in used_links:
        if link.source not in used_nodes:
            used_nodes.add(link.source)
        if link.sink not in used_nodes:
            used_nodes.add(link.sink)
    used_nodes = list(used_nodes)

    # Counts each time an edge in the original topology has been traversed by the path
    times_traversed = []
    for link1 in topology.links:
        z = 0
        for link2 in used_links:
            if link1.source.description == link2.source.description and link1.sink.description == link2.sink.description:
                z += 1   
            elif link1.sink.description == link2.source.description and link1.source.description == link2.sink.description:
                z += 1
        times_traversed.append((link1, z))
    
    # Makes binary vector representing assignment of component to node for the path:
    component_assignment = []
    for component in service.components:
        for node in topology.getLocationsByType("node"):
            if node.description + "_" + component.description in [i.description for i in used_nodes]: 
                component_assignment.append((component, node, 1))
            else:
                component_assignment.append((component, node, 0))

    path = service_path(topology.name + "_" + service.description, used_nodes, used_links, times_traversed, component_assignment)
    graph.addPath(path)
    return m



    





    

    