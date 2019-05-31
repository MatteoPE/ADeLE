import inspect
import os
from random import randint 
from mininext.topo import Topo
from mininext.services.quagga import QuaggaService
import pickle

net = None
IN_BW = 1000

class MyTopo(Topo):
    def __init__(self, confFile):
        Topo.__init__(self)
        self.confFile = confFile

        # Directory where this file / script is located"
        selfPath = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))  # script directory

        # Initialize a service helper for Quagga with default options
        quaggaSvc = QuaggaService(autoStop=False)

        # Path configurations for mounts
        try:
	    os.mkdir(selfPath + '/configs/')
        except OSError:
            pass
        quaggaBaseConfigPath = selfPath + '/configs/'
        
        # Initialize data structure to map each router with the port on the switch corresponding to incoming traffic
        self.in_interface = {}
        # saving speed of each interface
        self.intf_speed = {}
        # Initialize data structure to assign IP address to interfaces
        self.IP_interface = []
        self.numSubnets = 0

        routers = self.createTopologyFromConf(confFile, quaggaSvc, quaggaBaseConfigPath, r_name="r{:d}", s_name="s{:d}")

        # saving mapping on file
        with open('switch_mapping.pkl', 'wb+') as f:
            pickle.dump(self.in_interface, f)
            
        # saving intf speed on file
        with open('intf_speed.pkl', 'wb+') as f:
            pickle.dump(self.intf_speed, f)

        # saving ip addresses on file
        with open('configs/interfaces', 'w') as f:
            f.write('\n'.join(self.IP_interface))

    def createTopologyFromConf(self, confFile, quaggaSvc, quaggaBaseConfigPath, r_name, s_name):
        numRouters, links = readConfFile(confFile)
        routers = []
        switches = []
        for i in range(numRouters):
            quaggaContainer = self.addHost(name=r_name.format(i+1),
                                            hostname=r_name.format(i+1),
                                            privateLogDir=True,
                                            privateRunDir=True,
                                            inMountNamespace=True,
                                            inPIDNamespace=True,
                                            inUTSNamespace=True)
            quaggaSvcConfig = {'quaggaConfigPath': quaggaBaseConfigPath + r_name.format(i+1)}
            self.addNodeService(node=r_name.format(i+1), service=quaggaSvc, nodeConfig=quaggaSvcConfig)
            routers.append(quaggaContainer)
                    
        for idx, (r1, r2) in enumerate(links):
            sw = self.addSwitch(s_name.format(idx), protocols='OpenFlow13')
            switches.append(sw) 
            self.addLinkWithSwitch(routers[r1], routers[r2], switches[idx], bw=None)
        return routers
    
    def addLinkWithSwitch(self, r1, r2, s, bw=None):
        # start from 172.168.1.x
        self.numSubnets += 1
        if not bw:
            # from Ethernet 10Base-X to Gigabit Ethernet
            bw=randint(100, 800)
        self.addLink(r1,s, bw=bw)
        self.addLink(s,r2, bw=bw)
        # saving the port on the switch for incoming traffic on the specific router
        #self.in_interface.append("{:} {:} 2".format(r1, s))
        #self.in_interface.append("{:} {:} 1".format(r2, s))
        intf1 = self.addIntfSpeed(r1, bw)
        intf2 = self.addIntfSpeed(r2, bw)
        self.addIPAddress(r1, r2, intf1, intf2, self.numSubnets)

        if s not in self.in_interface:
            self.in_interface[s]={}
        self.in_interface[s][r1]=2
        self.in_interface[s][r2]=1
        

    def addIntfSpeed(self, router, bw):
        i = 0
        intf = ''
        while True:
            intf = '{:}-eth{:d}'.format(router, i)
            if intf.format(router, i) not in self.intf_speed:
                self.intf_speed[intf] = bw * 1000
                break
            i += 1
        return intf

    def addIPAddress(self, r1, r2, intf1, intf2, subnet):
        ip1 = '{:} {:} 172.168.{:}.1'.format(r1, intf1, subnet)
        self.IP_interface.append(ip1)
        ip2 = '{:} {:} 172.168.{:}.2'.format(r2, intf2, subnet)
        self.IP_interface.append(ip2)

def readConfFile(confFile):
    numRouters = 0
    links = []
    with open(confFile, 'r') as f:
        numRouters = int(f.readline())
        for link in f:
            r1, r2 = link.split()
            links.append((int(r1), int(r2)))
    return numRouters, links
