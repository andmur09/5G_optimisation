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
inf = 10000

class component(object):
    id_iter = itertools.count()
    ## Class representing a node (datacenter location)
        # \param id         Unique indtance id
        # \description      Description of component
        # \resources        Dictionary containing required resources: {cpu: float, ram: float}
    def __init__(self, description, requirements, replicas):
        self.id = next(component.id_iter)
        self.description = description
        self.requirements = requirements
        self.replicas = replicas
        
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
        self.graph = {}
    
    def getComponents(self):
        return self.components
    
    def addComponents(self, component):
        self.components.append(component)  

class service_graph(topology):
    def apsp():
        pass
