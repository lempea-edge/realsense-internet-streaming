import threading
import serial
import adafruit_gps
import time


class GPS(object):
    fetchThread = None
    gpsData = None
    gpsDataLock = threading.Lock()


    @classmethod
    def getGPSData(cls):
        return GPS.gpsData

    @classmethod
    def _fetchThread(cls, updateIntervalInSeconds=1):
        print("starting GPS data fetcher process!")

        uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)
        _gps = adafruit_gps.GPS(uart, debug=False)

        def fetchFromSerial():
            nonlocal uart
            nonlocal _gps

            _gps.update()
            if not _gps.has_fix:
                return {"latitude": "err", "longitude": "err", "speed": "err"}

            retVal = {
                "latitude": "{0:.6f}".format(_gps.latitude),
                "longitude": "{0:.6f}".format(_gps.longitude),
                "speed": "{}".format(_gps.speed_knots)
            }
            return retVal

        while True:
            GPS.gpsDataLock.acquire()
            GPS.gpsData = fetchFromSerial()
            GPS.gpsDataLock.release()
            time.sleep(updateIntervalInSeconds)

    @classmethod
    def startFetchThread(cls):
        if GPS.fetchThread is None:
            GPS.fetchThread = threading.Thread(
                target=GPS._fetchThread, kwargs={
                    "updateIntervalInSeconds": 1})
            GPS.fetchThread.start()

    @classmethod
    def stopFetchThread(cls):
        GPS.fetchThread = None