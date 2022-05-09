# -*- coding: utf-8 -*-
from topology_class import location, link, makeLink, topology
import optimisation

def main():
    # Makes the locations in the datacenter
    locations = []
    locations.append(location("Gateway", "gateway"))
    locations.append(location("Spine1", "switch"))
    locations.append(location("Leaf1", "switch"))
    locations.append(location("Leaf2", "switch"))
    locations.append(location("Node1", "node", resources={"cpu": float(4), "ram": float(8)}))
    locations.append(location("Node2", "node", resources={"cpu": float(2), "ram": float(16)}))

    # Makes the links between locations in the datacenter
    links = []
    links += makeLink(locations[0], locations[1], {"bandwidth": float(4), "latency": float(1)})
    links += makeLink(locations[1], locations[2], {"bandwidth": float(2), "latency": float(1)})
    links += makeLink(locations[1], locations[3], {"bandwidth": float(2), "latency": float(1)})
    links += makeLink(locations[2], locations[3], {"bandwidth": float(2), "latency": float(1)})
    links += makeLink(locations[2], locations[4], {"bandwidth": float(3), "latency": float(1)})
    links += makeLink(locations[2], locations[5], {"bandwidth": float(1), "latency": float(1)})
    links += makeLink(locations[3], locations[4], {"bandwidth": float(3), "latency": float(1)})
    links += makeLink(locations[3], locations[5], {"bandwidth": float(1), "latency": float(1)})
    
    # Creates then plots topology and saves to file
    problem = topology("trial1", locations, links)
    problem.plot()

    # Define source and sink for optimisation
    _from = problem.getLocationByDescription("Gateway")
    _to = problem.getLocationByDescription("Node1")

    result = optimisation.minCostFlow(problem, _from, _to)
if __name__ == "__main__":
    main()


