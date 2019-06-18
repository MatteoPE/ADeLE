#!/bin/bash

mn -c
/etc/init.d/quagga restart
rm -rf configs/ *.pkl
