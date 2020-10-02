import cv2
from base_camera_mp import BaseCamera
import pyrealsense2 as rs
import numpy as np
from turbojpeg import TurboJPEG
import multiprocessing

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

def _pipelineFunc():
    print("starting pipeline!")
    global rawFrames
    global pipeline
    global depth_scale
    pipeline = rs.pipeline()
    align = rs.align(rs.stream.color)
    colorizer = rs.colorizer()
    config = rs.config()
    config.enable_stream(rs.stream.color, w, h, rs.format.rgb8, 30)
    #config.enable_stream(rs.stream.infrared, 2, w, h, rs.format.y8, 30)
    config.enable_stream(rs.stream.depth, w, h, rs.format.z16, 30)
    profile = pipeline.start(config)
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    print("Depth scale is:", depth_scale)
    while True:
        rawFrameset = pipeline.wait_for_frames()
        fetchedColorFrame = np.asanyarray(rawFrameset.get_color_frame().get_data())
        #fetchedIRFrame = np.asanyarray(rawFrameset.get_infrared_frame(2).get_data())
        fetchedDepthFrame = np.asanyarray(align.process(rawFrameset).get_depth_frame().get_data())
        rawFrames.put({
        'rgb': fetchedColorFrame, 
        'depth': fetchedDepthFrame
        })

def _encodingFunc():
    print("starting encoder!")
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
        depth_max_input = 10000 # enforcing a max valid range of 10 meters on based on the realsense camera having a depth scale of 0.001. This is needed to allow for fast compression into a single JPEG without losing a lot of precision - further tuning of this value can be done (theoretical maximum of 65536 due to depth being sent from camera as 16-bit z16 format)
        # Compression into single JPEG is also needed as streaming this via
        # e.g. FFMPEG is possible in this manner
        scaling_factor = (depth_feature_range_max/depth_max_input)
        colorFrameCuda = cv2.cuda_GpuMat()
        colorFrameCuda.upload(colorFrame)
        colorFrame = cv2.cuda.cvtColor(colorFrameCuda, cv2.COLOR_BGR2RGB).download()
        depthFrame = (scaling_factor * depthFrame).astype('uint8')
        depthFrame = np.dstack((depthFrame, depthFrame, depthFrame))
        combinedFrame = np.hstack((colorFrame, depthFrame))
        combinedRetVal = jpeg.encode(combinedFrame)

        encodedFrames.put(combinedRetVal)

class Camera(BaseCamera):
    def __init__(self):
        super(Camera, self).__init__()

    @classmethod
    def get_jobs(self):
        global jobs
        return jobs

    @classmethod 
    def get_depth_scale(self):
        global depth_scale
        return depth_scale

    @staticmethod
    def get_raw_frames():
        global rawFrames
        if not rawFrames:
            return None

        if rawFrames.empty():
            return None

        return rawFrames.get()

    @classmethod
    def start_jobs(self):
        print("starting jobs...")
        global jobs
        global rawFrames
        global encodedFrames
        pipelineProcess = multiprocessing.Process(target=_pipelineFunc)
        encodingProcess = multiprocessing.Process(target=_encodingFunc)
        jobs = [pipelineProcess, encodingProcess]
        rawFrames = multiprocessing.Queue(10)
        encodedFrames = multiprocessing.Queue(10)
        for job in jobs:
            job.start()
        print("...started jobs!")

    @classmethod
    def terminate_jobs(self):
        global jobs
        global rawFrames
        global encodedFrames
        for job in jobs:
            job.terminate()
        rawFrames = None
        encodedFrames = None

    @staticmethod
    def frames():
        global encodedFrames
        while True:
            if not encodedFrames:
                continue

            if encodedFrames.empty():
                continue
            
            yield encodedFrames.get()
