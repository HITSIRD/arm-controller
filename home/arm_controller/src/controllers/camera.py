import time
import pyrealsense2 as rs
import numpy as np


class Camera:
    def __init__(self, width=640, height=480, fps=15):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)

        self.width = width
        self.height = height
        self.fps = fps

        self.started = False
        self.start()

    def start(self):
        try:
            self.pipeline.start()
            self.started = True
            print("[INFO] RealSense camera starting.")
            time.sleep(10)  # 给摄像头时间完成初始化
        except RuntimeError as e:
            print(f"[ERROR] Failed to start RealSense pipeline: {str(e)}")
            self.started = False
            raise

    def get_frame(self):
        try:
            frames = self.pipeline.wait_for_frames(10000)  # 等待帧，超时时间 10 秒
            color_frame = frames.get_color_frame()
            if not color_frame:
                print("[WARNING] No color frame received!")
                return None
            color_image = np.asanyarray(color_frame.get_data())
            return color_image
        except RuntimeError as e:
            print(f"[ERROR] Failed to retrieve frame: {str(e)}")
            return None