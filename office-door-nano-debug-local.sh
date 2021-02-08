#!/bin/bash
vserver="http://localhost:5037"
gpsserver="http://127.0.0.1:5037"

python3 realsense_nano_fake.py -v "${vserver}" -r 1 -g "${gpsserver}" --debug_images "true"

