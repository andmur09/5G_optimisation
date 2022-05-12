import sys
import gurobipy as gp
from gurobipy import GRB
from math import sqrt, log
import numpy as np
from topology_class import location, link, makeLink, topology
import graphviz as gvz

def minCostFlow(topology, _from, _to):
    m = gp.Model(topology.name + "_mcf")
    flow = m.addMVar(len(topology.getLinks()), lb = -1, ub=1, vtype=GRB.CONTINUOUS, name="flows")
    cost = np.ones(len(topology.getLinks()))
    
    # This will be defined in service class after. Placeholder for testing. Latency made arbitrarily high
    throughput = 2
    latency = 100

    toSkip = []
    for i in range(len(topology.links)):
        if i not in toSkip:
            linkA = topology.links[i]
            linkB = topology.getOpposingEdge(linkA)
            j = topology.links.index(linkB)
            # Adds bandwidth constraints for each link
            m.addConstr(flow[i] * throughput <= linkA.bandwidth)
            m.addConstr(flow[j] * throughput <= linkB.bandwidth)
            # Constrains flow from opposing links to be opposite
            m.addConstr(flow[i] == -flow[j])
            toSkip.append(j)
    
    for location in topology.locations:
        if location != _from and location != _to:
            incoming = topology.incomingEdge(location)
            outgoing = topology.outgoingEdge(location)
            incoming_indexes = [topology.links.index(i) for i in incoming]
            outgoing_indexes = [topology.links.index(i) for i in outgoing]
            # Adds conservation constraints at all locations in the datacenter except from source and sink nodes
            m.addConstr(gp.quicksum([flow[i] for i in incoming_indexes]) == gp.quicksum([flow[j] for j in outgoing_indexes]))
        elif location == _from:
            outgoing = topology.outgoingEdge(location)
            outgoing_indexes = [topology.links.index(i) for i in outgoing]
            # Adds constraint that total throughput leaves source node
            m.addConstr(gp.quicksum([flow[i] for i in outgoing_indexes]) == 1)
        elif location == _to:
            incoming = topology.incomingEdge(location)
            incoming_indexes = [topology.links.index(i) for i in incoming]
            # Adds constraint that total throughput leaves source node
            m.addConstr(gp.quicksum([flow[i] for i in incoming_indexes]) == 1)
    
    m.setObjective(cost @ flow, GRB.MINIMIZE)
    m.update()
    m.optimize()

    if m.status == GRB.OPTIMAL:
        print('\n objective: ', m.objVal)
        print('\n Vars:')
        for i in range(len(m.getVars())):
            print("Throughput from {} to {}: {}".format(topology.links[i].source.description, topology.links[i].sink.description, str(m.getVars()[i].x*throughput)))
    return m

def minCostFlowWithStops(topology, segments, plot=False):
    m = gp.Model(topology.name + "_mcfws")
    n_links = len(topology.getLinks())
    for i in range(len(topology.getLinks())):
        print(i, topology.getLinks()[i])
    n_segments = len(segments)
    # Makes flow matrix [w12(seg1),...,w1n(seg1),....wn1(seg1),...,wn-1(seg1)]
    #                   [w12(seg2),...,w1n(seg2),....wn1(seg2),...,wn-1(seg2)]
    #                                            ...
    #                   [w12(segm),...,w1n(segm),....wn1(segm),...,wn-1(segm)]
    flow = m.addMVar((n_segments, n_links), ub=1, vtype=GRB.CONTINUOUS, name="flows")
    cost = np.ones(n_links)
    # i = 0
    # for link in topology.getLinks():
    #     print(i, link.source.description, " - ", link.sink.description)
    #     i += 1
    
    # This will be defined in service class after. Placeholder for testing. Latency made arbitrarily high
    throughput = 2
    latency = 100

    toSkip = []
    for i in range(n_links):
        if i not in toSkip:
            linkA = topology.links[i]
            linkB = topology.getOpposingEdge(linkA)
            j = topology.links.index(linkB)
            # Skips opposing edge since we don't need to add it twice
            toSkip.append(j)
            # Adds bandwidth constraints for each link. Since flow is bi-directional need to constrain sum of opposing flows.
            # Also since we have multiple segments we must sum each.
            m.addConstr(gp.quicksum([flow[k,i] + flow[k,j] for k in range(n_segments)]) * throughput <= linkA.bandwidth)

    for k in range(n_segments):
        for location in topology.locations:
            incoming = topology.incomingEdge(location)
            outgoing = topology.outgoingEdge(location)
            incoming_indexes = [topology.links.index(i) for i in incoming]
            outgoing_indexes = [topology.links.index(i) for i in outgoing]
            # Adds conservation constraints at all locations in the datacenter.
            # Conservation is flow_out - flow_in = demand. Demand is how much the node consumes.
            # For source nodes there is more leaving than coming out in and therefore this is positive.
            # For sink nodes there is more coming in than leaving and so this is negative.
            if location.id not in [i.id for i in segments[k]]:
                m.addConstr(gp.quicksum([flow[k,i] for i in incoming_indexes]) == gp.quicksum([flow[k,j] for j in outgoing_indexes]))
            elif location.id == segments[k][0].id:
                # Constrains 100 percent of the flow to pass from the source so demand is 1.
                m.addConstr(gp.quicksum([flow[k,i] for i in outgoing_indexes]) - gp.quicksum([flow[k,j] for j in incoming_indexes]) == 1)
            else:
                # Constraints 100 percent of the flow to pass into the sink
                m.addConstr(gp.quicksum([flow[k,i] for i in outgoing_indexes]) - gp.quicksum([flow[k,j] for j in incoming_indexes]) == -1)
    m.setObjective(sum(flow[k] @ cost for k in range(n_segments)), GRB.MINIMIZE)
    m.update()
    m.write("trial1.lp")
    m.write("trial1.mps")
    m.optimize()

    if m.status == GRB.OPTIMAL:
        print('\n objective: ', m.objVal)
        print('\n Vars:')
        for v in m.getVars():
            print("Variable {}: ".format(v.varName) + str(v.x))
    else:
        m.computeIIS()
        m.write("trial1.ilp")
    
    # If plot is True it plots the graph showing the flows.
    if plot == True:
        plot = gvz.Digraph(format='png')
        for location in topology.getLocations():
            plot.node(name=str(location.id), label=location.description)
        for k in range(n_segments):
            for i in range(len(topology.getLinks())):
                source_id = topology.getLinks()[i].source.id
                sink_id = topology.getLinks()[i].sink.id
                plot.edge(str(source_id), str(sink_id), label="w{}{}{}: {}".format(k, source_id, sink_id, flow[k, i].x), color="/spectral9/"+str(k))
        plot.render('{}_plot.gv'.format(m.ModelName), view=True)
    return m