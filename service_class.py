from glob import escape
import sys
import this
import graphviz as gvz
import subprocess
import copy
import logging
import itertools
from topology_class import *
from numpy import inf
from make_service_graph import make_graph
inf = 10000

class component(object):
    id_iter = itertools.count()
    ## Class representing a node (datacenter location)
        # \param id         Unique indtance id
        # \description      Description of component
        # \resources        Dictionary containing required resources: {cpu: float, ram: float}
    def __init__(self, description, requirements, replica_count):
        self.id = next(component.id_iter)
        self.description = description
        self.requirements = requirements
        self.replica_count = replica_count
        
    def getName(self):
        return self.id
    
    def __str__(self):
        return "Component: {}, Description: {}".format(self.id, self.description)
    
    @property
    def required_cpu(self):
        return self.requirements["cpu"]

    @property
    def required_ram(self):
        return self.requirements["ram"]

class service(object):
    ## Class representing a node (datacenter location)
        # \param id         Unique indtance id
        # \description      Description of service
        # \components       List of required components in service
    def __init__(self, description, components, required_throughput, required_latency):
        self.description = description
        self.components = components
        self.required_throughput = required_throughput
        self.required_latency = required_latency
        self.graphs = {}
        self.paths = []
    
    def getComponents(self):
        return self.components
    
    def addComponents(self, component):
        self.components.append(component)  
    
    def addGraph(self, _topology):
        # Given a topology it makes the equivalent service graph and initialises the paths as an empyt list
        nodes, edges = make_graph(self, _topology)
        self.graphs[_topology.name] = service_graph(_topology.name + "_" + self.description, nodes, edges)

    def getGraph(self, topology):
        try:
            return self.graphs[topology.name]
        except KeyError:
            print("No graph for given topology. Try using service.addGraph(topology) to create one")
            return None


class service_graph(topology):
    def __init__(self, name, locations, links):
        super().__init__(name, locations, links)
        self.paths = []

    def addPath(self, path):
        self.paths.append(path)
    
    def getPaths(self):
        return self.paths
    
    def getStartNode(self):
        for i in self.locations:
            incoming = [l for l in self.getLinks() if l.sink == i]
            if not incoming:
                return i
    
    def getEndNode(self):
        for i in self.locations:
            outgoing = [l for l in self.getLinks() if l.source == i]
            if not outgoing:
                return i

class service_path(topology):
    id_iter = itertools.count()
    def __init__(self, name, locations, links, times_traversed, component_assignment):
        super().__init__(name, locations, links)
        self.name = name + str(next(location.id_iter))
        self.times_traversed = times_traversed
        self.component_assignment = component_assignment