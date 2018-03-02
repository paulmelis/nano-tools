#!/usr/bin/env python
import sys, os
scriptdir = os.path.split(__file__)[0]
sys.path.insert(0, os.path.join(scriptdir, '..'))

import nanodb

db = nanodb.NanoDatabase('nano.db')

t = db.account_tree(True)
print(len(t))

assert 0 in t           # Genesis
assert len(t[0]) == 2   # Genesis -> Landing + Faucet

def write_edge_list_csv(e):
    with open('atree.csv', 'wt') as f:
        f.write('Source;Target\n')
        for account, children in t.items():
            for c in children:
                f.write('%d;%d\n' % (account, c))
            
def create_igraph_graph(t):
    
    import igraph
        
    ids = set()
    for account, children in t.items():
        ids.add(account)
        for c in children:
            ids.add(c)
    maxid = max(ids)

    g = igraph.Graph(directed=True)
    g.add_vertices(maxid+1)
    edges = []
    for account, children in t.items():
        for c in children:
            edges.append((account, c))
    g.add_edges(edges)
    #assert g.is_dag()
    #assert True not in g.is_multiple()
    #layout = g.layout_reingold_tilford()
    #layout = g.layout_fruchterman_reingold()
    
    return g
    
import numpy

childcount = []
for account, children in t.items():
    childcount.append(len(children))
    for c in children:
        if c not in t:
            childcount.append(0)
            
childcount = numpy.array(childcount)
childcount = numpy.sort(childcount)
