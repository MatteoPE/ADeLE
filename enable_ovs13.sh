#!/bin/bash

switches=(s1 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 s12 s13 s14 s15 s16)

for s in "${switches[@]}"
do
    ovs-vsctl set bridge $s protocols=OpenFlow10,OpenFlow12,OpenFlow13
done
#vs-vsctl set bridge s1 protocols=OpenFlow10,OpenFlow12,OpenFlow13

