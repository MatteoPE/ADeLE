# MiniNExT + Quagga

## Ubuntu 

- Install Ubuntu 14.04 (http://releases.ubuntu.com/14.04/) on a Virtual Machine.

- Downgrade your Linux Kernel to 3.x.x (follow [this](https://itsfoss.com/upgrade-linux-kernel-ubuntu/) tutorial).

- Update Ubuntu
```
sudo apt-get update
sudo apt-get install git -y
```

## Mininet 

- Install Mininet version 2.1.0 
```
sudo apt-get install mininet=2.1.0-0ubuntu1
```

- Test Mininet
```
sudo mn --test pingall
```

## Quagga

- Install Quagga version 0.99.22.4-3ubuntu1.5
```
sudo apt-get install quagga
```

- Create the links to the dynamic libraries
```
sudo ldconfig
``` 

## MiniNExT

- Install MiniNExT
```
git clone https://github.com/USC-NSL/miniNExT.git
cd MiniNExT/
sudo apt-get install `make deps`
sudo make install
```

- Test MiniNExT
```
cd MiniNExT/examples/quagga-ixp/
sudo ./start.py
```

## Ryu (optional)

- Install Ryu
```
sudo apt-get install python-setuptools python-pip -y
sudo apt-get install python-eventlet python-routes python-webob python-paramiko -y

sudo pip install tinyrpc ovs oslo.config msgpack-python eventlet enum34
sudo pip install eventlet --upgrade

git clone git://github.com/osrg/ryu.git
cd ryu/
sudo python ./setup.py install
```

- Test Ryu
```
ryu-manager
```
If some modules are missing,
```
sudo pip install <module>
```