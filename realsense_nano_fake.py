import cv2
from base_camera_mp import BaseCamera
import numpy as np
import multiprocessing
import atexit
import argparse
import signal
import sys
import time
import requests
from os import path

# Set up Intel RealSense camera pipeline
pipeline = None
depth_scale = None

# Set up frame queues
rawFrames = None
encodedFrames = None
jobs = None

# TurboJPEG encoder instance
jpeg = None #TurboJPEG()

# Application arguments
video_destination = None
gps_destination = None
retry_interval = None
stream_id = None
w = None
h = None
frame_rate = None
debug = False
# Cannot be enabled on command line currently
debug_write = False

def gen_frame():
    global encodedFrames
    frameNumberDebug = 3000

    while True:
        frame = encodedFrames.get()
        if debug_write:
            barr = bytes(frame)
            with open("debug-images/{:04d}".format(frameNumberDebug), 'wb') as f:
                f.write(barr)
            frameNumberDebug += 1

        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
               b'\r\n' + frame + b'\r\n')


def gen_frame_fake():
    debug = True
    frameNumberDebug = 1
    while True:
        time.sleep(0.01)
        debugFile = "debug-images/{:04d}".format(frameNumberDebug)
        if not path.exists(debugFile):
            sys.exit(0)
            frameNumberDebug = 1
            debugFile = "debug-images/{:04d}".format(frameNumberDebug)
        if not path.exists(debugFile):
            print("Error: debug images dir or file ", debugFile, "does not exist!")
        with open(debugFile, 'rb') as f:
            print("Frame number: ", frameNumberDebug)
            frame = f.read()
            frameNumberDebug += 1

            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
                   b'\r\n' + frame + b'\r\n')

def _sendVideoData():
    global encodedFrames
    global destination
    global debug

    framegen=gen_frame()
    if debug:
        framegen=gen_frame_fake()

    while True:
        try:
            r = requests.post(
                video_destination,
                data=framegen,
                headers={
                    "Content-Type": "multipart/x-mixed-replace; boundary=--frame;",
                    "Content-Resolution": str(2*w) + "x" + str(h) + "x3",
                    "Stream-ID": stream_id},
                verify=True)
        except Exception as e:
            print(e)
            print("_sendVideoData failed. Retrying in", retry_interval, "second(s)")
            time.sleep(retry_interval)

def _sendGPSData():
    try:
        GPS.startFetchThread()
        while True:
            r = requests.post(gps_destination, json=GPS.getGPSData(), verify=True)
            # verify=False causes requests to not verify the origin of the
            # server's SSL certificate, which is useful in development e.g.
            # when working with self-signed certificates. This option should be
            # *True* in production.
            time.sleep(1)
    except Exception as e:
        print(e)
        print("_sendGPSData failed. Retrying in", retry_interval, "second(s)")
        time.sleep(retry_interval)


def start_jobs():
    print("Starting jobs...")
    global jobs
    global rawFrames
    global encodedFrames
    videoSendingProcess = multiprocessing.Process(target=_sendVideoData)
    gpsSendingProcess = multiprocessing.Process(target=_sendGPSData)
    jobs = [videoSendingProcess, gpsSendingProcess]
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
    parser.add_argument(
        "-x",
        "--frame_width",
        help="The width of the camera image frame in pixels.",
        default=640,
        type=int
    )
    parser.add_argument(
        "-d",
        "--debug_images",
        help="Use debug images instead of real input video.",
        default="false",
        type=str
    )
    parser.add_argument(
        "-y",
        "--frame_height",
        help="The height of the camera image frame in pixels.",
        default=480,
        type=int
    )
    parser.add_argument(
        "-f",
        "--frame_rate",
        help="The framerate of the camera video input (fps).",
        default=30,
        type=int
    )

    args = parser.parse_args()
    video_destination = args.video_destination
    gps_destination = args.gps_destination
    retry_interval = args.retry_interval
    stream_id = args.stream_id
    w = int(args.frame_width)
    h = int(args.frame_height)
    frame_rate = int(args.frame_rate)
    debug = args.debug_images == "true"

    signal.signal(signal.SIGINT, exit_signal_handler)

    start_jobs()
