import sys
import gurobipy as gp
from gurobipy import GRB
from math import sqrt, log
import numpy as np
from topology_class import location, link, makeLink, topology

T = 2

m = gp.Model("flow")
w112 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w112")
w113 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w113")
w124 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w124")
w134 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w134")
w121 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w121")
w131 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w131")
w142 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w142")
w143 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w143")

w212 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w212")
w213 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w213")
w224 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w224")
w234 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w234")
w221 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w221")
w231 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w231")
w242 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w242")
w243 = m.addVar(lb = 0, ub=1, vtype=GRB.CONTINUOUS, name="w243")


# Flow constraints for flow 1
m.addConstr(w112 + w113 - w121 - w131== 1)
m.addConstr(w124 + w121 - w112 - w142 == 0)
m.addConstr(w134 + w131 - w113 - w143 == 0)
m.addConstr(w142 + w143 - w124 - w134 == -1)

# Flow constraints for flow 2
m.addConstr(w212 + w213 - w221 - w231== -1)
m.addConstr(w224 + w221 - w212 - w242 == 0)
m.addConstr(w234 + w231 - w213 - w243 == 0)
m.addConstr(w242 + w243 - w224 - w234 == 1)

# Throughput constraints
m.addConstr((w112 + w121 + w212 + w221)* T <= 5)
m.addConstr((w113 + w131 + w213 + w231) * T <= 5)
m.addConstr((w124 + w142 + w224 + w242) * T <= 5)
m.addConstr((w134 + w143 + w234 + w243) * T <= 5)

m.setObjective(w112 + w113 + w124 + w134 + w121 + w131 + w142 + w143 + w212 + w213 + w224 + w234 + w221 + w231 + w242 + w243, GRB.MINIMIZE)
m.update()
m.optimize()

m.write("trial2.lp")
if m.status == GRB.OPTIMAL:
    print('\n objective: ', m.objVal)
    print('\n Vars:')
    for v in m.getVars():
        print("Variable {}: ".format(v.varName) + str(v.x))
#𝑤12 −𝑤21=1
#(𝑤21+𝑤23+𝑤24)−(𝑤12+𝑤32+𝑤42)=0
#(𝑤42+𝑤43)−(𝑤24+𝑤34)=0
#(𝑤32+𝑤34)−(𝑤23+𝑤43)=−1
