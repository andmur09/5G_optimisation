# -*- coding: utf-8 -*-
from unicodedata import bidirectional

from pyparsing import col
from topology_class import *
from service_class import *
from make_service_graph import *
from optimisation import columnGeneration
#import optimisation

def main():
    # Makes the locations in the datacenter
    locations = []
    locations.append(location("Gateway", "gateway"))
    locations.append(location("Spine1", "spine"))
    locations.append(location("Leaf1", "leaf"))
    locations.append(location("Leaf2", "leaf"))
    locations.append(location("Node1", "node", resources={"cpu": float(4), "ram": float(8)}))
    locations.append(location("Node2", "node", resources={"cpu": float(2), "ram": float(16)}))

    # Makes the links between locations in the datacenter
    links = []
    link1 = link(locations[0], locations[1], {"bandwidth": float(10), "latency": float(1)})
    link2 = link(locations[1], locations[2], {"bandwidth": float(5), "latency": float(1)})
    link3 = link(locations[1], locations[3], {"bandwidth": float(5), "latency": float(1)})
    link4 = link(locations[2], locations[3], {"bandwidth": float(5), "latency": float(1)}, two_way=True)
    link5 = link(locations[2], locations[4], {"bandwidth": float(5), "latency": float(1)})
    link6 = link(locations[2], locations[5], {"bandwidth": float(5), "latency": float(1)})
    link7 = link(locations[3], locations[4], {"bandwidth": float(5), "latency": float(1)})
    link8 = link(locations[3], locations[5], {"bandwidth": float(5), "latency": float(1)})
    for i in (link1, link2, link3, link4, link5, link6, link7, link8):
        links.append(i)

    # Creates then plots topology and saves to file
    problem = topology("topology_test", locations, links)
    # gateway = problem.getGateway()

    # Creates a service with two components
    c1 = component("component1", {"cpu": 1, "ram": 2}, 2)
    c2 = component("component2", {"cpu": 1, "ram": 2}, 2)
    s = service("service_test", [c1, c2], 1, 10)
    layers = problem.getLocationsByTypes()

    # Gets service graph using topology
    s.addGraph(problem)
    graph = s.getGraph(problem)
    graph.plot()
    
    m = columnGeneration(problem, s)
    for path in graph.paths:
        print([l.description for l in path.links])
    #problem.print()

    # Define source and sink for optimisation
    # _from = problem.getLocationByDescription("Gateway")
    # _to = problem.getLocationByDescription("Node1")
    # result = optimisation.minCostFlow(problem, stops)
    
    # # Defines source/sink pairs for each flow
    # gateway = problem.getLocationByDescription("Gateway")
    # node = problem.getLocationByDescription("Node1")
    # segments = [(gateway, node), (node, gateway)]

    # result = optimisation.minCostFlowWithStops(problem, segments, plot=True)
    
if __name__ == "__main__":
    main()


