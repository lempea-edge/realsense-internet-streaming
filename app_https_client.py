import cv2
from base_camera_mp import BaseCamera
import pyrealsense2 as rs
import numpy as np
from turbojpeg import TurboJPEG
import multiprocessing
import atexit
import argparse
import signal
import sys
import time
import requests
from gps import GPS

# Set up Intel RealSense camera pipeline
w, h = 640, 480
pipeline = None
depth_scale = None

# Set up frame queues
rawFrames = None
encodedFrames = None
jobs = None

# TurboJPEG encoder instance
jpeg = TurboJPEG()

# Application arguments
video_destination = None
gps_destination = None
retry_interval = None
stream_id = None


def gen_frame():
    global encodedFrames

    while True:
        frame = encodedFrames.get()
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
               b'\r\n' + frame + b'\r\n')


def _sendVideoData():
    global encodedFrames
    global destination

    while True:
        try:
            r = requests.post(
                video_destination,
                data=gen_frame(),
                headers={
                    "Content-Type": "multipart/x-mixed-replace; boundary=--frame;",
                    "Content-Resolution": "1280x480x3",
                    "Stream-ID": stream_id},
                verify=True)
        except Exception as e:
            print(e)
            print("_sendVideoData failed. Retrying in", retry_interval, "second(s)")
            time.sleep(retry_interval)


def _pipelineFunc():
    print("Starting pipeline...")
    global rawFrames
    global pipeline
    global depth_scale
    pipeline = rs.pipeline()
    align = rs.align(rs.stream.color)
    colorizer = rs.colorizer()
    config = rs.config()
    config.enable_stream(rs.stream.color, w, h, rs.format.rgb8, 30)
    config.enable_stream(rs.stream.depth, w, h, rs.format.z16, 30)
    profile = pipeline.start(config)
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    print("Depth scale is:", depth_scale)
    while True:
        rawFrameset = pipeline.wait_for_frames()
        fetchedColorFrame = np.asanyarray(
            rawFrameset.get_color_frame().get_data())
        fetchedDepthFrame = np.asanyarray(
            align.process(rawFrameset).get_depth_frame().get_data())
        rawFrames.put({
            'rgb': fetchedColorFrame,
            'depth': fetchedDepthFrame
        })


def _encodingFunc():
    print("Starting encoder...")
    global rawFrames
    global encodedFrames

    while True:
        if not rawFrames:
            continue

        if rawFrames.empty():
            continue

        rawFrame = rawFrames.get()
        colorFrame = rawFrame['rgb']
        depthFrame = rawFrame['depth']

        depth_feature_range_min = 0
        depth_feature_range_max = 255
        # enforcing a max valid range of 10 meters on based on the realsense
        # camera having a depth scale of 0.001. This is needed to allow for
        # fast compression into a single JPEG without losing a lot of precision
        # - further tuning of this value can be done (theoretical maximum of
        # 65536 due to depth being sent from camera as 16-bit z16 format)
        depth_max_input = 10000
        # Compression into single JPEG is also needed as streaming this via
        # e.g. FFMPEG is possible in this manner
        scaling_factor = (depth_feature_range_max / depth_max_input)
        colorFrameCuda = cv2.cuda_GpuMat()
        colorFrameCuda.upload(colorFrame)
        colorFrame = cv2.cuda.cvtColor(
            colorFrameCuda, cv2.COLOR_BGR2RGB).download()
        depthFrame = (scaling_factor * depthFrame).astype('uint8')
        depthFrame = np.dstack((depthFrame, depthFrame, depthFrame))
        combinedFrame = np.hstack((colorFrame, depthFrame))
        combinedRetVal = jpeg.encode(combinedFrame)

        encodedFrames.put(combinedRetVal)


def _sendGPSData():
    try:
        r = requests.post(gps_destination, json=GPS.getGPSData(), verify = False)
        # verify=False causes requests to not verify the origin of the
        # server's SSL certificate, which is useful in development e.g.
        # when working with self-signed certificates. This option should be
        # *True* in production.
    except Exception as e:
        print(e)
        print("_sendGPSData failed. Retrying in", retry_interval, "second(s)")
        time.sleep(retry_interval)


def start_jobs():
    print("Starting jobs...")
    global jobs
    global rawFrames
    global encodedFrames
    pipelineProcess = multiprocessing.Process(target=_pipelineFunc)
    encodingProcess = multiprocessing.Process(target=_encodingFunc)
    videoSendingProcess = multiprocessing.Process(target=_sendVideoData)
    gpsSendingProcess = multiprocessing.Process(target=_sendGPSData)
    jobs = [pipelineProcess, encodingProcess, videoSendingProcess, gpsSendingProcess]
    rawFrames = multiprocessing.Queue(10)
    encodedFrames = multiprocessing.Queue(10)
    for job in jobs:
        job.start()


def terminate_jobs():
    try:
        global jobs
        global rawFrames
        global encodedFrames

        if jobs is not None:
            for job in jobs:
                job.terminate()

        rawFrames = None
        encodedFrames = None
    except Exception as e:
        print(e)


def exit_signal_handler(sig, frame):
    print('Exiting because Ctrl+C was pressed.')
    sys.exit(0)


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s is not a valid positive int value" % value)
    return ivalue


if __name__ == "__main__":
    atexit.register(terminate_jobs)
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--video_destination",
        help="Full HTTPS path to destination for video data",
        default="https://127.0.0.1:5038",
        type=str
    )
    parser.add_argument(
        "-g",
        "--gps_destination",
        help="Full HTTPS path to destination for GPS data",
        default="https://127.0.0.1:5039",
        type=str
    )
    parser.add_argument(
        "-r",
        "--retry_interval",
        help="Interval (in seconds) after which application will attempt to establish HTTPS link again after a failure.",
        default=2,
        type=check_positive
    )
    parser.add_argument(
        "-s",
        "--stream_id",
        help="StreamID is a string that uniquely identifies the video stream to the destination.",
        default="default-streamID",
        type=str
    )

    args = parser.parse_args()
    video_destination = args.video_destination
    gps_destination = args.gps_destination
    retry_interval = args.retry_interval
    stream_id = args.stream_id

    signal.signal(signal.SIGINT, exit_signal_handler)

    start_jobs()
