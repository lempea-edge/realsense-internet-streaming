#!/bin/bash
set -euxo pipefail
cp /usr/lib/x86_64-linux-gnu/librealsense2.so.2.44 .
docker build --no-cache -t rainedge/realsense .

