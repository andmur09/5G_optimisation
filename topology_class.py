# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 11:55:20 2021

@author: kpb20194
"""
import sys
import graphviz as gvz
import subprocess
import copy
import logging
import itertools
import numpy as np
inf = 10000

def key_exists(dictionary, keys):
    ## Check if *keys (nested) exists in `element` (dict).
    if not isinstance(dictionary, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _dictionary = dictionary
    for key in keys:
        try:
            _dictionary = _dictionary[key]
        except KeyError:
            return False
    return True 

class location(object):
    id_iter = itertools.count()
    ## Class representing a node (datacenter location)
        # \param id         Unique indtance id
        # \description      String descpription of location
        # \type             One of "switch", "gateway" or "node"
        # \resources        If node, dictionary containing resources: {"cpu": float, "ram": float}
    def __init__(self, description, type, resources=None):
        self.id = next(location.id_iter)
        self.description = description
        if type not in ("switch", "gateway", "node", "artificial_source", "artificial_sink"):
            raise AttributeError("Invalid location type. type must be 'switch', 'gateway', 'node', 'artificial_source' or 'artificial_sink'.")
        if type == "node" and resources == None:
            raise AttributeError("Location of type node must have resources. Define using resources = \{'cpu': float, 'ram': float\}.")
        elif type != "node" and resources != None:
            raise AttributeError("Only location of type node should have resources")
        else:
            self.resources = resources
        self.type = type

    def getName(self):
        return self.id
    
    def __str__(self):
        return "Location: {}, Description: {}".format(self.id, self.description)
    
    def copy(self):
        return location(self.description[:], self.type[:], copy.deepcopy(self.resources))
    
    @property
    def cpu(self):
        if self.type == "node":
            return self.resources["cpu"]
        else:
            raise AttributeError

    @property
    def ram(self):
        if self.type == "node":
            return self.resources["ram"]
        else:
            raise AttributeError
    
class link(object):
    ## Class representing an edge (link) between two locations in the datacenter
        # \param description    String name describing link
        # \param soure          Start node in the link (instance of location class)
        # \param sink           End node in the link (instance of location class)
        # \param parameters     Dictionary containing link parameters: {"bandwidth": float, "latency": float}

    def __init__(self, source, sink, parameters):
        self.source = source
        self.sink = sink
        self.id = "C({}, {})".format(source.id, sink.id)
        self.parameters = parameters

    def copy(self):
        return link(self.source, self.sink, copy.deepcopy(self.parameters))
    
    def getID(self):
        return self.id

    def getSource(self):
        return self.source

    def getSink(self):
        return self.sink
    
    def setLatency(self, latency):
        self.parameters["latency"] = latency
    
    def setBandwidth(self, bandwidth):
        self.parameters["bandwidth"] = bandwidth

    
    def __str__(self):
        return "Link {} ({}) -> {} ({})".format(self.source.description, self.source.id, self.sink.description, self.sink.id)

    def forJSON(self):
        ### To be updated
        jsonDict = {"end_event_name": self.sink, "type": self.type, "name": self.description}
        jsonDict["properties"] = {}
        if self.type == "stc" or self.type == "stcu":
            jsonDict["properties"]["lb"] = self.lb
            jsonDict["properties"]["ub"] = self.ub
        elif self.type == "pstc":
            if self.distribution["type"] == "uniform":
                jsonDict["properties"]["distribution"] = {"type": "Uniform", "lb": self.dist_lb, "ub": self.dist_ub}
            elif self.distribution["type"] == "gaussian":
                jsonDict["properties"]["distribution"] = {"type": "Gaussian", "mean": self.mu, "variance": self.sigma}
        jsonDict["start_event_name"] = self.source
        return jsonDict

    @property
    def bandwidth(self):
        return self.parameters["bandwidth"]

    @property
    def latency(self):
        return self.parameters["latency"]

class topology(object):
    def __init__(self, name, locations, links):
        ## Class representing the datacenter topology. A graph of locations and links
        # \param name           String name of topology
        # \param locations      List of instances of location class
        # \param links          List of instances of link class
        self.name = name
        self.locations = locations
        self.links = links

    def setName(self, name):
        self.name = name
    
    def makeCopy(self, name):
        return topology(name,  self.locations[:], [link.copy() for link in self.links])

    def getLinks(self):
        return self.links

    def getLocations(self):
        return self.locations
    
    def getLocationByDescription(self, description):
        result = None
        for location in self.locations:
            if location.description == description:
                result = location
        return result
    
    def getEdgeByLocations(self, source_id, sink_id):
        # Given two locations it returns the link
        result = None
        for link in self.links:
            if link.source.id == source_id and link.sink.id == sink_id:
                result = link
            elif link.sink.id == source_id and link.source.id == sink_id:
                result = link
        return result 

    def getSwitches(self):
        return [i for i in self.getLocations() if i.type == "switch"]

    def getNodes(self):
        return [i for i in self.getLocations() if i.type == "node"]

    def getGateway(self):
        return [i for i in self.getLocations() if i.type == "gateway"]
    
    def getArtificialSource(self):
        return [i for i in self.getLocations() if i.type == "artificial_source"]

    def getArtificialSink(self):
        return [i for i in self.getLocations() if i.type == "artificial_sink"]

    def outgoingEdge(self, location):
        return [l for l in self.getLinks() if l.source == location]
    
    def incomingEdge(self, location):
        return [l for l in self.getLinks() if l.sink == location]
    
    def getOpposingEdge(self, link):
        opposing = [l for l in self.getLinks() if l.source == link.sink and l.sink == link.source]
        if opposing:
            if len(opposing) == 1:
                return opposing[0]
            else:
                raise ValueError("Edge cannot have more than one opposing edge.")
        else:
            return None

    def addLink(self, source, sink, parameters):
        new_link = link(source, sink, parameters)
        self.links.append(new_link)
        print("Link Added")

    def addLocation(self, location):
        self.locations.append(location)
    
    def getLocationByID(self, id):
        for location in self.getLocations():
            if id == location.id:
                return location
        print("No location found with that ID.")
        return False

    def pstnJSON(self):
        # To be updated
        constList = []
        for constraint in self.constraints:
            constList.append(constraint.forJSON())
        toWrite = {self.name: constList}
        try:
            f = open("{}.json".format(self.name), "x")
            f.write(str(toWrite))
            f.close()
            print("File successfully created")
            return True
        except FileExistsError:
            print("File name already in use. Try changing name of PSTN to something not in use")
            answer = input("Change name of PSTN? [Y/N]: ")
            if answer == "Y" or answer == "y":
                newName = input("Input new name: ")
                self.setName(newName)
                self.pstnJSON()
            else:
                print("File creation failed")
                return False
            
    def plot(self):
        ## Plots the topology to a file using graphviz
        plot = gvz.Digraph(format='png')
        for location in self.getLocations():
            plot.node(name=str(location.id), label=location.description)
        
        for link in self.getLinks():
            plot.edge(str(link.source.id), str(link.sink.id), label="L: {}, B: {}".format(link.latency, link.bandwidth))
        try:
            plot.render('{}_plot.gv'.format(self.name), view=True)
        except subprocess.CalledProcessError:
            print("Please close the PDF and rerun the script")

    def print(self, write=False):
        for link in self.getLinks():
            print("\n")
            print("Description: ", link.id)
            print("Latency: {}, Bandwidth: {}".format(link.latency, link.bandwidth))
            print("Source: ", link.source.id, link.source.description)
            print("\tType: ", link.source.type)
            if link.source.type == "node":
                print("\tCPU: ", link.source.cpu)
                print("\tRAM: ", link.source.ram)
            print("Sink: ", link.sink.id, link.sink.description)
            print("\tType: ", link.sink.type)
            if link.sink.type == "node":
                print("\tCPU: ", link.sink.cpu)
                print("\tRAM: ", link.sink.ram)
    
    def addArtificialSource(self, connections):
        # Adds an artifical source node connected to each node in list 'connections'. If connections contains one location 'A' then it will add a link source->A
        source = location("Artificial Source", "artificial_source")
        self.addLocation(source)
        for i in connections:
            self.addLink(source, i, {"bandwidth": np.inf, "latency": 0})

    def addArtificialSink(self, connections):
        # Adds an artifical sink node connected to each node in list 'connections'. If connections contains one location 'B' then it will add a link B -> Sink
        sink = location("Artificial Sink", "artificial_sink")
        self.addLocation(sink)
        for i in connections:
            self.addLink(i, sink, {"bandwidth": np.inf, "latency": 0})

def makeLink(locationA, locationB, parameters):
    ## If given two locations in the datacenter, A and B, this function makes two links A -> B and B -> A (since data is bidirectional)
    link1 = link(locationA, locationB, parameters)
    link2 = link(locationB, locationA, parameters)
    return [link1, link2]
