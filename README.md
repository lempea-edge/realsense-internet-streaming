### Overview
This repository implements a server application for streaming JPEG-compressed
color and depth images derived from raw color and depth information obtained
from an Intel RealSense D455 camera connected to the device on which the server
is running.
The application runs separate Python processes for 1) fetching the raw data
from the Intel RealSense camera, 2) encoding the raw data into compressed
JPEGs, 3) serving the JPEGs to each connected client

### Development environment
The application has been tested to run successfully on Python 3.7.6
on a machine running Ubuntu 20.04.1 LTS x86_64 and Intel® RealSense™ SDK 2.0 (v2.38.1).

### Dependencies
#### Intel RealSense SDK installed with Python bindings
This can be achieved through manual compilation via:
https://github.com/IntelRealSense/librealsense/tree/development/wrappers/python

Note: In the case of a target machine with a specification matching the
development environment, the same can be achieved by installing RealSense SDK from
offical repositories as instructed under
https://github.com/IntelRealSense/librealsense/blob/master/doc/distribution_linux.md
and then installing the pyrealsense2 Python package via:
```
pip install pyrealsense2
```
(see https://pypi.org/project/pyrealsense2/)

#### Python packages
The extra Python packages required to run this application are listed in
requirements.txt, and can be installed using:
```
pip install -r requirements.txt
```

### Acknowledgements
The observer pattern implementation used for serving the JPEG frames to
multiple clients is borrowed from:
https://github.com/miguelgrinberg/flask-video-streaming/tree/v1