import sys
import gurobipy as gp
from gurobipy import GRB
from math import sqrt, log
import numpy as np
from topology_class import location, link, makeLink, topology

def minCostFlow(topology, _from, _to):
    m = gp.Model(topology.name + "_mcf")
    flow = m.addMVar(len(topology.getLinks()),lb = -1, ub=1, vtype=GRB.CONTINUOUS, name="flows")
    
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
            m.addConstr(flow[i] * throughput <= link.bandwidth)
            m.addConstr(flow[j] * throughput <= link.bandwidth)
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
            



        topology.links.index(topology.getOpposingEdge(link))
        m.addConstr(flow[i] * throughput <= link.bandwidth)
        pairs.append((i, ))

        link1 = i
        link2 = topology.getOpposingEdge(topology.links[i])


    n = len(vars)
    m = 2 * len(cc)
    p = 2 * len(cu)
    r = len(rvars)

    c = np.zeros(n)
    A = np.zeros((m, n))
    b = np.zeros(m)
    T = np.zeros((p, n))
    q = np.zeros((p))
    mu_X = np.zeros((r))
    cov_X = np.zeros((r, r))
    psi = np.zeros((p, r))

    # Gets matrices for controllable constraints in form Ax <= b
    for i in range(len(cc)):
        ub = 2 * i
        lb = ub + 1
        start_i, end_i = vars.index(cc[i].source.id), vars.index(cc[i].sink.id)
        A[ub, start_i], A[ub, end_i], b[ub] = -1, 1, cc[i].intervals["ub"]
        A[lb, start_i], A[lb, end_i], b[lb] = 1, -1, -cc[i].intervals["lb"]
        if cc[i].hard == False:
            ru_i = vars.index(cc[i].name + "_ru")
            #rl_i = vars.index(cc[i].name + "_rl")
            A[ub, ru_i], c[ru_i] = -1, 1
            #A[lb, rl_i], c[rl_i] = -1, inf
    
    # Gets matrices for joint chance constraint P(Psi omega <= T * vars + q) >= 1 - alpha
    for i in range(len(cu)):
        ub = 2 * i
        lb = ub + 1
        incoming = PSTN.incomingContingent(cu[i])
        if incoming["start"] != None:
            incoming = incoming["start"]
            start_i, end_i = vars.index(incoming.source.id), vars.index(cu[i].sink.id)
            T[ub, start_i], T[ub, end_i] = 1, -1
            T[lb, start_i], T[lb, end_i] = -1, 1
            q[ub] = cu[i].intervals["ub"]
            q[lb] = -cu[i].intervals["lb"]
            if cu[i].hard == False:
                ru_i = vars.index(cu[i].name + "_ru")
                #rl_i = vars.index(cu[i].name + "_rl")
                T[ub, ru_i], c[ru_i] = 1, 1
                #T[lb, rl_i], c[rl_i] = 1, inf
            rvar_i = rvars.index("X" + "_" + incoming.source.id + "_" + incoming.sink.id)
            psi[ub, rvar_i] = -1
            psi[lb, rvar_i] = 1
            mu_X[rvar_i] = incoming.mu
            cov_X[rvar_i][rvar_i] = incoming.sigma**2
        elif incoming["end"] != None:
            incoming = incoming["end"]
            start_i, end_i = vars.index(cu[i].source.id), vars.index(incoming.source.id)
            T[ub, start_i], T[ub, end_i] = 1, -1
            T[lb, start_i], T[lb, end_i] = -1, 1
            q[ub] = cu[i].intervals["ub"]
            q[lb] = -cu[i].intervals["lb"]
            if cu[i].hard == False:
                ru_i = vars.index(cu[i].name + "_ru")
                #rl_i = vars.index(cu[i].name + "_rl")
                T[ub, ru_i], c[ru_i] = 1, 1
                #T[lb, rl_i], c[rl_i] = 1, inf
            rvar_i = rvars.index("X" + "_" + incoming.source.id + "_" + incoming.sink.id)
            psi[ub, rvar_i] = 1
            psi[lb, rvar_i] = -1
            mu_X[rvar_i] = incoming.mu
            cov_X[rvar_i][rvar_i] = incoming.sigma**2
        else:
            raise AttributeError("Not an uncontrollable constraint since no incoming pstc")

    # Performs transformation of X into eta where eta = psi X such that eta is a p dimensional random variable
    mu_eta = psi @ mu_X
    cov_eta = psi @ cov_X @ psi.transpose()

    # Translates random vector eta into standard form xi = N(0, R) where R = D.eta.D^T
    D = np.zeros((p, p))
    for i in range(p):
        D[i, i] = 1/sqrt(cov_eta[i, i])
    R = D @ cov_eta @ D.transpose()
    T = D @ T
    q = D @ (q - mu_eta)
    mu_xi = np.zeros((p))
    cov_xi = R
    return A, vars, b, c, T, q, mu_xi, cov_xi