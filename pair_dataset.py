import os
import re
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dir',
                    type=str,
                    default='.')
parser.add_argument('--dataset',
                    type=str,
                    default='dataset_final')
args = parser.parse_args()
DIRECTORY = args.dir
DATASET = args.dataset
DATASET_PATH = os.path.join(DIRECTORY, DATASET)
OUTPUT_PATH = os.path.join(DIRECTORY, 'models_final')

def make_dir(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)


# for all the different run
for run in os.listdir(DATASET_PATH):
    dir_content = os.listdir(os.path.join(DATASET_PATH, run))
    # getting the capture file
    for content in dir_content:
        if 'capture' in content:
            capture = content
            break

    cap_file = os.path.join(DATASET_PATH, run, capture)
    print(cap_file)
    with open(cap_file, 'r') as cap_f:
        #do something
        counters = cap_f.readlines()
        # reading all the paths associated to that run
        with open(os.path.join(DATASET_PATH, run, 'paths.txt'), 'r') as path_f:
            make_dir(OUTPUT_PATH)
            # creating a folder for every src,dst pair
            for line in path_f:
                target, path = line.strip().split(':')
                target = re.sub('[ .]+', '_', target)
                folder = os.path.join(OUTPUT_PATH, target)

                make_dir(folder)
                path = [int(hop) for hop in path.split()]
                next_hop = path[1]
                label = np.zeros(10, dtype=np.int)
                label[next_hop] = 1
				# writing the dataset in the final form: packet_counter, next_hop
                dataset_file = 'dataset_final{:}'.format(run)
                with open(os.path.join(folder, dataset_file), 'w+') as f:
                    label = ' '.join(str(i) for i in label)+'\n'
                    for counter in counters:
                        line = counter.strip() + ', ' + label
                        f.write(line)

