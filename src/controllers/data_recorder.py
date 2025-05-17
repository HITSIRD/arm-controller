import os
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class DataRecorder(QThread):
    data_saved = pyqtSignal()

    def __init__(self, arm, hand, camera, save_path, save_interval=1 / 30):
        super().__init__()
        self.arm = arm
        self.hand = hand
        self.camera = camera
        self.save_path = save_path
        self.save_interval = save_interval
        self.running = False
        self.pose_data = []
        self.force_data = []
        self.tactile_data = []
        self.image_obs_data = []

    def run(self):
        self.running = True
        while self.running:
            timestamp = time.time()
            position, orientation = self.arm.get_pose()
            widths = self.hand.read_widths()
            # forces = self.hand.read_forces()
            # tactile = self.hand.read_tactile()
            image_obs = self.camera.get_image()

            self.pose_data.append([timestamp, *position, *orientation, *widths])
            # self.force_data.append([timestamp, *forces])
            # self.tactile_data.append([timestamp, *tactile])
            self.image_obs_data.append(image_obs)
            time.sleep(self.save_interval)

    def stop_and_save(self):
        self.running = False
        os.makedirs(self.save_path, exist_ok=True)
        np.save(os.path.join(self.save_path, 'pose.npy'), np.array(self.pose_data))
        np.save(os.path.join(self.save_path, 'force.npy'), np.array(self.force_data))
        np.save(os.path.join(self.save_path, 'tactile.npy'), np.array(self.tactile_data))
        self.data_saved.emit()