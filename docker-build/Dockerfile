FROM rainedge/tf-cv:latest
LABEL maintainer="Eemil Lagerspetz eemil.lagerspetz@lempea.com"

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,video,utility

RUN git clone https://github.com/lempea-edge/realsense-internet-streaming.git

WORKDIR /realsense-internet-streaming

RUN pip3 --no-cache-dir install -r requirements.txt

RUN apt-get update && apt-get -y install ffmpeg libturbojpeg

ADD librealsense2.so.2.44 /realsense-internet-streaming/

ENTRYPOINT ["/usr/bin/python3", "app_https_client.py"]
