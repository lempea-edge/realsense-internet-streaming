#!/usr/bin/env python
from flask import Flask, Response
from camera_realsense_mp import Camera
from gps import GPS
import datetime

app = Flask(__name__)
GPS.startFetchThread()

def nSecondsHavePassedSince(n, lastEpoch):
    delta = datetime.datetime.now() - lastEpoch
    return int(delta.seconds * 1000 + delta.microseconds / 1000) > (n * 1000)

def gen(camera):
    while True:
        frame = camera.get_frame_all()
        yield (b'--frame\r\n'
        b'Content-Type:image/jpeg\r\n'
        b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
        b'\r\n' + frame + b'\r\n')

@app.route('/video_feed_realsense')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=--frame')

@app.route('/location_feed_adafruit')
def location_feed():
   """GPS data route. Returns the latest recorded GPS data snapshot to the client."""
   return GPS.getGPSData()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5037', threaded=True, debug=False, ssl_context='adhoc')
