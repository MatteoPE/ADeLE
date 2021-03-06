#!/usr/bin/python
"""
Example network of Quagga routers
(QuaggaTopo + QuaggaService)
"""

import sys
sys.path.insert(0, './ryu')
# import ryu.my_routes as routes
import my_routes as routes

import stat
import os
import pickle
import random
from conf_topo import MyTopo
# from mininext.net import MiniNExT
# from mininext.cli import CLI
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.util import dumpNodeConnections
# import sys
import atexit
import itertools
import argparse
# patch isShellBuiltin
import re
import time
import mininet.util
# import mininext.util
# mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

parser = argparse.ArgumentParser(description='Start data generation')
parser.add_argument('--file',
                    type=str,
                    default='10-16-5.txt',
                    help='Configuration file')
args = parser.parse_args()
CONFFILE = args.file

# list of target for which iperf doesn't work (don't know the reason)
# blacklist = [('r2', 'ri3'), ('r2', 'ri4'), ('r3', 'r6'), ('r4', 'r1'),
#             ('r4', 'ri3'), ('r5', 'ri2'), ('r6', 'r3'), ('ri3', 'r5')]

DEF_PSW = 'zebra'
REF_BANDWIDTH = 1000  # bw for OSPF cost calculation, goes in the ospf conf file
SIM_DURATION = 120  # seconds of traffic simulation duration
TRAFFIC_PROB = 0.65  # probability of sending traffic between a pair of routers
ITERATION = 1  # number of iteration for the dataset generation
DATASET_DIR = 'dataset_final'
CONFIG_PATH = "configs"
net = None


def startNetwork():
    "instantiates a topo, then starts the network and prints debug information"

    paths = routes.Net()

    try:
        os.mkdir(DATASET_DIR)
    except OSError:
        pass


    for i in range(ITERATION):
        try:
            os.mkdir(DATASET_DIR + '/run{:}'.format(i))
            print(os.chmod(DATASET_DIR + '/run{:}/'.format(i), 0777))

        except OSError:
            pass

        info('** Creating Quagga network topology\n')
        mytopo = MyTopo(CONFFILE)

        info('** Starting the network\n')
        global net
        net = Mininet(topo=mytopo, build=False, controller=RemoteController, switch=OVSKernelSwitch, link=TCLink)
        # c = net.addController(
        #     'c0',
        #     controller=RemoteController,
        #     ip='127.0.0.1',
        #     port=6633)
        c = RemoteController('c0', ip='127.0.0.1', port=6633)
        net.addController(c)

        net.build()
        net.start()

        info('** Configuring addresses on interfaces\n')
        setInterfaces(net, "configs/interfaces")
        
        #testRouter(net)
        #CLI(net)
        net.run(simulateTraffic, mytopo, net, SIM_DURATION, i, paths)
        # cleaning the paths object for the next run
        paths.reset()

def testRouter(net):
    info('*** Test\n')
    for r in net.hosts:
        r.cmdPrint('sysctl net.ipv4.ip_forward=1')
        r.cmdPrint('zebra -f configs/{:}/zebra.conf -d -i configs/{:}/zebra.pid > configs/{:}/zebra.log 2>&1'.format(r, r, r))
        r.waitOutput()
        r.cmdPrint('ospfd -f configs/{:}/ospfd.conf -d -i configs/{:}/ospfd.pid > configs/{:}/ospfd.log 2>&1'.format(r, r, r))
        r.waitOutput()
    time.sleep(60)


def simulateTraffic(topo, net, duration, iteration, paths):
    
    # for sw in topo.list_s:
    #     os.system("ovs-vsctl set bridge {:} protocols=OpenFlow10,OpenFlow12,OpenFlow13".format(sw))
                    
    
    info('***RUN {:}'.format(iteration))
    info('\n** Waiting for OSPF to converge\n')
    #time.sleep(60)
    testRouter(net)
    # saving the routing table corresponding to the current run
    info('** Dumping routing table\n')

    if os.system(
            'cd utils && bash getRoutingTable.sh && cd - > /dev/null') != 0:
        error('Can\'t dump routing table, exiting...')
        exit(-1)

        # the paths obj contains all the newtork information, including all the
        # available paths and the routers configuration
    paths.parse_routes(routes.ROUTES_FILE, routes.ROUTER_CONF, save_mapping=True)
    paths.get_paths()
    paths.save_paths(DATASET_DIR + '/run{:}/paths.txt'.format(iteration))
    valid = []
    with open('addresses.pkl', 'rb') as f:
            # contains the addresses of each router
        rout_addr = pickle.load(f)

    with open('addr_rout.pkl', 'rb') as f:
            # contains the router of each address
        addr_rout = pickle.load(f)

        # starting the iperf server on all the routers
    start_iperf(net.hosts)

    valid_addr = []
    # retrieving the hosts addresses
    for host in net.hosts:
        valid_addr.extend(rout_addr[host.name])

    info('***Starting traffic simulation\n')
    # list of (src_router, dst_ip)
    combinations = list(itertools.product(net.hosts, valid_addr))

    start = time.time()
    while time.time() < start + duration:
        random.shuffle(combinations)
        # print(combinations)
        for s, d in combinations:
            d_name = addr_rout[d]
            p = random.random()
            if is_valid_path(s.name, d_name) and p > TRAFFIC_PROB:
                s.cmd('iperf -t {:} -c {:} &'.format(random.randint(1, 10), d))

    stop_iperf(net.hosts)


def start_iperf(hosts):
    for host in hosts:
        info('*** Starting iperf server on {:}\n'.format(host.name))
        host.cmd('pkill iperf')
        # using & allows to nonblocking cmd
        host.cmd('iperf -s &')


def stop_iperf(hosts):
    for host in hosts:
        info('*** Stopping iperf server on {:}\n'.format(host.name))
        host.cmd('pkill iperf')


def is_valid_path(s, d):
    if s == d:
        return False

        # not generating traffic from and to inner routers
    if 'i' in s or 'i' in d:
        return False

    if (s, d) in blacklist:
        return False

    return True


def setInterfaces(net, intfFile):
    # conf file: router interface address
    networks = {}
    zebra_conf = {}
    # loading intf speed
    with open('intf_speed.pkl', 'rb') as f:
        intf_speed = pickle.load(f)

    with open(intfFile) as conf:
        for line in conf.readlines():
            params = line.strip()
            if params and params[0] == "#":
                continue
            elif params:
                router, interface, ip = params.split(" ")
#                print(params)
                net.get(router).setIP(ip, 24, interface)
                # checking if switch or router
                if "s" in router:
                    continue

                if router not in networks:
                    networks[router] = set([])
                networks[router].add(getNetwork(ip, 24) + "/24 area 0")

                bw = intf_speed[interface]
                if router not in zebra_conf:
                    zebra_conf[router] = []
                zebra_conf[router].append((interface, ip, bw))

        # the zebra config needs to be recomputed because at each run we're
        # changing the interface speed
    createZebraConfig(zebra_conf)
    # the OSPF configuration doesn't need to be reconfigured every time unless you change the ip addresses or the reference bandwidth
    createOSPFConfig(networks)


def createOSPFConfig(networks):
    for router in networks:
        OSPF_path = CONFIG_PATH + '/' + router + "/ospfd.conf"
        with open(OSPF_path, "w+") as conf:
            conf.write("hostname {:}\n".format(router))
            conf.write("\nlog file {:}/{:}/ospfd.log\n".format(CONFIG_PATH, router))
            conf.write("\nrouter ospf\n")
            conf.write(
                "auto-cost reference-bandwidth {:}\n".format(REF_BANDWIDTH))
            for network in networks[router]:
                conf.write("  network {:}\n".format(network))
        os.system("chown quagga:quagga {:}".format(OSPF_path))
        os.system("chmod 640 {:}".format(OSPF_path))

        


def createZebraConfig(zebra_conf):
    for router in zebra_conf:
        zebra_path = CONFIG_PATH + '/' + router + '/zebra.conf'
        with open(zebra_path, 'w+') as conf:
            conf.write("hostname {:}\n".format(router))
            conf.write("password {:}\n\n".format(DEF_PSW))
            for config in zebra_conf[router]:
                intf, addr, bw = config
                conf.write("interface {:}\n".format(intf))
                conf.write("\tip address {:}/24\n".format(addr))
                conf.write("\tbandwidth {:d}\n".format(bw))
                conf.write("\tlink-detect\n\n")
        os.system("chown quagga:quagga {:}".format(zebra_path))
        os.system("chmod 640 {:}".format(zebra_path))

# get network address from host, to be implemented
def getNetwork(address, prefix):
    return re.sub(r"([0-9]+\.[0-9]+\.[0-9]+)\.[0-9]+", "\\1.0", address)


def stopNetwork():
    "stops a network (only called on a forced cleanup)"

    if net is not None:
        info('** Tearing down Quagga network\n')
        net.stop()
    os.system("killall -9 ospfd zebra quagga")
    os.system("rm -rf configs/*")
    os.system("mn -c >/dev/null 2>&1")


if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stopNetwork)

    # Tell mininet to print useful information
    setLogLevel('info')
    startNetwork()
