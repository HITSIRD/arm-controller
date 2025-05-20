import os
import time
import threading
import numpy as np

from home.arm_controller.src.controllers.arm_controller import ArmController
from home.arm_controller.src.controllers.hand_controller import HandController


class DataRecorder(threading.Thread):
    def __init__(self, arm, hand, camera, save_path, save_interval=1 / 10, callback=None):
        super().__init__()
        self.arm = ArmController(arm)
        self.hand = HandController(hand)
        self.camera = camera
        self.save_path = save_path
        self.save_interval = save_interval
        self.running = threading.Event()
        self.pose_data = []
        self.force_data = []
        self.tactile_data = []
        self.image_obs_data = []
        self.callback = callback  # Optional callback for when data is saved
        self.frame_count = 0
    def run(self):
        self.running.set()

        while self.running.is_set():
            timestamp = time.time()

            image_obs = self.camera.get_frame() if self.camera is not None else None
            # 采集运动学与图像数据
            position, orientation = self.arm.get_pose()
            widths = [self.hand.read_width()]
            # 存储数据
            self.pose_data.append([timestamp, *position, *orientation, *widths])
            #print("appended")
            if image_obs is not None:
                self.image_obs_data.append(image_obs)
            self.frame_count += 1
            process_time = time.time()-timestamp
            # 动态调整睡眠时间，确保总间隔接近 save_interval
            sleep_time = max(0.0, self.save_interval - process_time)
            time.sleep(sleep_time)


        # 线程结束时保存数据
        self.save_data()

    def stop_and_save(self):
        self.running.clear()
        self.join()  # 等待 run() 方法结束

    def save_data(self):
        os.makedirs(self.save_path, exist_ok=True)
        print("Saving data...")
        print(f"sum frame count: {self.frame_count}")
        np.save(os.path.join(self.save_path, 'pose.npy'), np.array(self.pose_data))
        if self.camera is not None:
            np.save(os.path.join(self.save_path, 'camera.npy'), np.array(self.image_obs_data))
        # 若需要：保存力或触觉数据
        # np.save(os.path.join(self.save_path, 'force.npy'), np.array(self.force_data))
        # np.save(os.path.join(self.save_path, 'tactile.npy'), np.array(self.tactile_data))

        if self.callback:
            self.callback()
