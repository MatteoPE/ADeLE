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

        routers = self.createTopologyFromConf(confFile)

        # saving mapping on file
        with open('switch_mapping.pkl', 'wb+') as f:
            pickle.dump(self.in_interface, f)
            
        # saving intf speed on file
        with open('intf_speed.pkl', 'wb+') as f:
            pickle.dump(self.intf_speed, f)

    def createTopologyFromConf(self, confFile):
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
            switches.append(self.addSwitch(s_name.format(count + i + 1),protocols='OpenFlow13'))
        
        for idx, l in links: 
            self.addLinkWithSwitch(routers[l[0]], routers[l[1]], switches[idx], bw)
        return routers
    
    def addLinkWithSwitch(self, r1, r2, s, bw=None):
        if not bw:
            # from Ethernet 10Base-X to Gigabit Ethernet
            bw=randint(100, 800)
        self.addLink(r1,s, bw=bw)
        self.addLink(s,r2, bw=bw)
        # saving the port on the switch for incoming traffic on the specific router
        #self.in_interface.append("{:} {:} 2".format(r1, s))
        #self.in_interface.append("{:} {:} 1".format(r2, s))
        self.addIntfSpeed(r1, bw)
        self.addIntfSpeed(r2, bw)

        if s not in self.in_interface:
            self.in_interface[s]={}
        self.in_interface[s][r1]=2
        self.in_interface[s][r2]=1
        

    def addIntfSpeed(self, router, bw):
        i = 0
        while True:
            intf = '{:}-eth{:d}'.format(router, i)
            if intf.format(router, i) not in self.intf_speed:
                self.intf_speed[intf] = bw * 1000
                break
            i += 1

def readConfFile(confFile):
    numRouters = 0
    links = []
    with open(confFile, 'r') as f:
        numRouters = int(f.readline())
        for link in f:
            r1, r2 = link.split()
            links.append((int(r1), int(r2)))
    return numRouters, links
