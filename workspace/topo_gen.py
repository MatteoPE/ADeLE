import random
import argparse
import string
from itertools import combinations

parser = argparse.ArgumentParser(description='Specify the parameters for the topology')
parser.add_argument('--v',
                    type=int,
                    default=10,
                    help='Number of vertices')
parser.add_argument('--max_e',
                    type=int,
                    default=16,
                    help='Max number of edges')
parser.add_argument('--alpha',
                    type=float,
                    default=0.5,
                    help='Probability that two vertices are connected')
args = parser.parse_args()
# num of vertices
V = int(args.v)
# max num of edges
MAX_E = int(args.max_e)
# edge probability
ALPHA = float(args.alpha)

def biased_coin(alpha):
    if random.random() < alpha:
        return True 
    return False

def generate_edges():
    edges = []
    all_edges = [item for item in combinations(range(V), 2)]
    random.shuffle(all_edges)
    for e in all_edges:
        if biased_coin(ALPHA):
            edges.append(e)
        if len(edges) >= MAX_E:
            break
    return edges
    
def is_connected(edges):
    # cc = connected component (see https://en.wikipedia.org/wiki/Component_(graph_theory))
    cc = V*[-1]
    num_cc = 0
    # check how many connected components are in the grpah
    for v1, v2 in edges:
        if cc[v1] == -1:
            if cc[v2] == -1:
                # first edge for both vertices --> new cc
                cc[v1] = num_cc
                cc[v2] = num_cc
                num_cc += 1
            else:
                # v2 in a cc, v1 not in a cc --> v1 in v2's cc
                cc[v1] = cc[v2]
        else:
            if cc[v2] == -1:
                # v1 in a cc, v2 not in a cc --> v2 in v1's cc
                cc[v2] = cc[v1]
            else:
                # both vertices in a cc -> all vertices in v2's cc join v1's cc
                for idx, v in enumerate(cc):
                    if v == cc[v2]:
                        cc[idx] == cc[v1]
    # true if all the vertices are in the same cc
    for v in cc:
        if v != cc[0]:
            return False
    return True

if __name__ == '__main__':
    filename = "{}-{}-{}.txt".format(V, MAX_E, str(ALPHA).replace('0.',''))
    with open(filename, 'w') as f:
        f.write("{}\n".format(V))
        edges = generate_edges()
        while not is_connected(edges):
            edges = generate_edges()
        for e in edges:
            f.write("{} {}\n".format(e[0], e[1]))
