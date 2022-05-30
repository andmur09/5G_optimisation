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

def compact(topology, services, paths):
    m = gp.Model(topology.name + "_compact")
    n_paths = len(paths)
    n_services = len(services)
    n_links = len(topology.links)

    # Makes variable matrix of path,service pairs.
    # Represents the fraction of the total throughput of service j, passing through path i
    #                     [x_p1,s1,...,x_p1,s2,...,x_p1,sS]
    #                     [x_p2,s1,...,x_p2,s2,...,x_p2,sS]
    #                                 ...
    #                     [x_pP,s1,...,x_pP,s2,...,x_pP,sS]
    xsp = m.addMVar((n_paths, n_services), vtype=GRB.CONTINUOUS, name="xps")
    # Same as above but multiplied by required service throughput. The total flow contribution of service
    # j in path i
    fsp = m.addMVar((n_paths, n_services), vtype=GRB.CONTINUOUS, name="fps")
    # Makes binary matrix of link,path pairs
    # 1 if link i is on path j else 0
    #                     [x_l1,p1,...,x_l1,p2,...,x_l1,pP]
    #                     [x_l2,p1,...,x_l2,p2,...,x_l2,pP]
    #                                 ...
    #                     [x_lL,p1,...,x_lL,p2,...,x_lL,pP]
    xlp = m.addMVar((n_links, n_paths), vtype=GRB.BINARY, name="xlp")

    # Variable defining total link utilisation cost. This is the sum of the link cost and the amount of traffic
    # being used by the link across all services and paths
    luc = m.addMVar(shape=n_links, vtype=GRB.CONTINUOUS, name="link_utilization_cost")
    
    for i in range(len(services)):
        for j in range(len(paths)):
            for k in range(len(services[i].components)):
                m.addVar(vtype=GRB.BINARY, name = "y_{}{}{}".format[k,])

    # Multiplies the fractional flow by the total service throughput to get actual throughput of a service j on path i
    throughputs =[j.throughput for j in services]
    for i in range(n_paths):
        for j in range(n_services):
            m.addConstr(fsp[i,j] == xsp[i,j] * throughputs[j])

    # Ensures that the total service demand is met across all paths:
    for j in range(n_services):
        m.addConstr(gp.quicksum([xsp[i,j] for i in range(n_paths)]) >= 1)

    # This constrains the link utilisation cost to be the sum of the service demands used by the link over the lilnk bandwidth multiplied by the link cost 
    for i in range(n_links):
        m.addConstr(luc[i] == (topology.links[i].cost * gp.quicksum(xlp @ fsp)[i]) /topology.links[i].bandwidth)

    

    