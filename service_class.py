import sys
import graphviz as gvz
import subprocess
import copy
import logging
import itertools
inf = 10000

class component(object):
    id_iter = itertools.count()
    ## Class representing a node (datacenter location)
        # \param id         Unique indtance id
        # \description      Description of component
        # \resources        Dictionary containing required resources: {cpu: float, ram: float}
    def __init__(self, description, requirements):
        self.id = next(component.id_iter)
        self.description = description
        self.requirements = requirements
        
    def getName(self):
        return self.id
    
    def __str__(self):
        return "Component: {}, Description: {}".format(self.id, self.description)
    
    def make_replica(self):
        return component(self.description[:], copy.deepcopy(self.requirements))
    
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
    
    def getComponents(self):
        return self.components
    
    def addComponents(self, component):
        self.components.append(component)