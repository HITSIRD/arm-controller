import os
import json
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from src.controllers.data_recorder import DataRecorder
from src.controllers.motion_threads import MotionThread

class RobotControlUI(QWidget):
    def __init__(self, arm, hand, camera):
        super().__init__()
        self.arm = arm
        self.hand = hand
        self.camera = camera
        self.recorder = None

        # with open('/home/robotarm/lcl/ljn/collect_img_data/data_index.json', 'r') as f:
        #     self.data_index = json.load(f)['index']
        #
        # self.save_path = f'/home/robotarm/new_dirve/20250510_LFF/arm_hand/data_{self.data_index}'
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        buttons = [
            ("开始记录", self.start_recording),
            ("结束记录", self.stop_recording),
            ("恢复初始位", self.recover_position),
            ("执行动作：放置", lambda: self.run_motion('q_lemon.txt', 'dq_lemon.txt')),
            ("执行动作：远离", lambda: self.run_motion('q_lemon_away.txt', 'dq_lemon_away.txt', 6500)),
            ("执行动作：关闭", lambda: self.run_motion('q_close.txt', 'dq_close.txt', 13000))
        ]

        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        self.setLayout(layout)
        self.setWindowTitle("机械臂与灵巧手控制")

    def start_recording(self):
        if not self.recorder or not self.recorder.isRunning():
            self.recorder = DataRecorder(self.arm, self.hand, self.save_path)
            self.recorder.data_saved.connect(lambda: print("数据保存完成"))
            self.recorder.start()
            print("数据记录开始")

    def stop_recording(self):
        if self.recorder and self.recorder.isRunning():
            self.recorder.stop_and_save()
            self.recorder.wait()
            self.recorder = None

    def recover_position(self):
        self.hand.set_angles([1000]*5 + [0])
        j_goto = np.array([-2.015, 1.44, 2.183, -1.85, -1.01, 2.15, 0.043])
        self.arm.move_to(j_goto)

    def run_motion(self, q_file, dq_file, max_step=None):
        thread = MotionThread(
            arm=self.arm,
            q_path=os.path.join('action', q_file),
            dq_path=os.path.join('action', dq_file),
            max_step=max_step
        )
        thread.finished.connect(lambda: print(f"动作 {q_file} 完成"))
        thread.start()