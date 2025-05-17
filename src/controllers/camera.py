import pyrealsense2 as rs
# import cv2
import numpy as np
import time


class Camera:
    def __init__(self, width=512, height=512, fps=30):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)

        self.width = width
        self.height = height
        self.fps = fps

        self.started = False

    def start(self):
        self.pipeline.start(self.config)
        self.started = True
        print("[INFO] RealSense camera started.")

    def get_frame(self):
        if not self.started:
            raise RuntimeError("Camera not started. Call start() first.")
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            return None, None
        color_image = np.asanyarray(color_frame.get_data())
        timestamp = frames.get_timestamp()
        return color_image, timestamp

    def stop(self):
        self.pipeline.stop()
        self.started = False
        print("[INFO] RealSense camera stopped.")
