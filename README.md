## Overview
This repository implements a server application for streaming JPEG-compressed
color and depth images derived from raw color and depth information obtained
from an Intel RealSense D455 camera connected to the device on which the server
is running.
The application runs separate Python processes for 1) fetching the raw data
from the Intel RealSense camera, 2) encoding the raw data into compressed
JPEGs, 3) serving the JPEGs to each connected client.
## Development Environment
Jetson Nano (Developer Kit Version)  
Ubuntu 18.04.4 LTS (GNU/Linux 4.9.140-tegra aarch64)  
Jetpack 4.4 [L4T 32.4.3]  
CUDA 10.2.89  
OpenCV 4.4.1 (with CUDA)  
Python 3.6.9  
## Dependencies
### Intel RealSense SDK installed with Python bindings
For the Jetson Nano, this can be achieved through manual compilation via:  
https://github.com/jetsonhacks/installRealSenseSDK/blob/master/buildLibrealsense.sh
### LibJpegTurbo and PyTurboJPEG
LibJpegTurbo's Jpeg encoder is significantly faster than OpenCV's Jpeg encoder. It uses SIMD instructions 
to speed up the encoding process. PyTurboJPEG is a wrapper for LibJpegTurbo.  
Setup instructions can be found at:  
https://pypi.org/project/PyTurboJPEG/
### OpenCV with CUDA compute capabilities
For the Jetson Nano, OpenCV with CUDA compute capabilities can be set up via
the instructions provided at:  
https://github.com/JetsonHacksNano/buildOpenCV
### Python packages
The extra Python packages required to run this application are listed in
requirements.txt, and can be installed using:
```
pip3 install -r requirements.txt
```
In case the Numpy installation via pip3 throws an error related to the package
'Cython' not being found, run the following before re-running the command
above:
```
pip3 install Cython
```
## Running
### Client / Server Mode
To run the application as a server from which multiple clients can connect and fetch video data, run as follows:  
```
python3 app_mp.py
```
### Point-to-Point Mode
To run the application in point-to-point mode where it pushes video data over HTTPS to a single specific destination, run as follows:  
```
python3 app_https_client.py -v https://<host>:<port> -g https://<path_to_host_gps_route> -r <retry_interval>  
```
For this latter mode, you need to have an appropriate HTTPS listener **already running** on the specified destination, before starting the application on the Nano.  
One option is to use the freely available ffmpeg tool (see https://ffmpeg.org/ffmpeg.html):  
```
ffmpeg -listen 1 -key_file server.key -cert_file server.crt -i https://<host>:<port> -f <desired output format/destination>
```
Note: ```<host>``` and ```<port>``` refer to the IP address and the port of the destination which the HTTPS listener will monitor for incoming traffic.  
```<path_to_host_gps_route>``` refers to the full path (hostname + url) to which the GPS data has to be sent.  
```<retry_interval>``` refers to the waiting period, in seconds, after which the application will automatically try to re-establish an HTTPS connection with the destination, if the previous connection attempt failed.  
To enable https based operation, you will need to provide an appropriate SSL certificate and key to the HTTPS listener.
## Acknowledgements
The observer pattern implementation used for serving the JPEG frames to
multiple clients is borrowed from:  
https://github.com/miguelgrinberg/flask-video-streaming