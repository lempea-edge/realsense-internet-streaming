### Overview
This repository implements a server application for streaming JPEG-compressed
color and depth images derived from raw color and depth information obtained
from an Intel RealSense D455 camera connected to the device on which the server
is running.
The application runs separate Python processes for 1) fetching the raw data
from the Intel RealSense camera, 2) encoding the raw data into compressed
JPEGs, 3) serving the JPEGs to each connected client


### Dependencies
#### Intel RealSense SDK installed with Python bindings
For the Jetson Nano, this can be achieved through manual compilation via:
https://github.com/jetsonhacks/installRealSenseSDK/blob/master/buildLibrealsense.sh

#### LibJpegTurbo and PyTurboJPEG
LibJpegTurbo's Jpeg encoder is significantly faster than OpenCV's Jpeg encoder. It uses SIMD instructions 
to speed up the encoding process. PyTurboJPEG is a wrapper for LibJpegTurbo. Setup instructions can be found at:
https://pypi.org/project/PyTurboJPEG/

#### OpenCV with CUDA compute capabilities
For the Jetson Nano, OpenCV with CUDA compute capabilities can be set up via the instructions provided at:
https://github.com/JetsonHacksNano/buildOpenCV

#### Python packages
The extra Python packages required to run this application are listed in
requirements.txt, and can be installed using:
```
pip3 install -r requirements.txt
```

### Acknowledgements
The observer pattern implementation used for serving the JPEG frames to
multiple clients is borrowed from:
https://github.com/miguelgrinberg/flask-video-streaming/tree/v1