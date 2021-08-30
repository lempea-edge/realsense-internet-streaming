#!/bin/bash

# let camera wake up
sleep 50

source /home/lempeanano1/realsense-internet-streaming/settings-flow.sh
/usr/bin/python3 app_https_client.py -v "${rain}${vnode}" -r 1
