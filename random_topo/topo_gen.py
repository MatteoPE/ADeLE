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
    

if __name__ == '__main__':
    filename = "{}-{}-{}.txt".format(V, MAX_E, str(ALPHA).replace('0.',''))
    with open(filename, 'w') as f:
        f.write("{}\n".format(V))
        edges = generate_edges()
        for e in edges:
            f.write("{} {}\n".format(e[0], e[1]))
