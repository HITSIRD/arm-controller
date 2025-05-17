import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class MotionThread(QThread):
    finished = pyqtSignal()

    def __init__(self, arm, q_path, dq_path, max_step=None, length=15):
        super().__init__()
        self.arm = arm
        self.q_path = q_path
        self.dq_path = dq_path
        self.max_step = max_step
        self.length = length

    def run(self):
        q = np.loadtxt(self.q_path)
        dq = np.loadtxt(self.dq_path)

        self.arm.move_to(q[0])
        ctrl = self.arm.create_controller()
        self.arm.create_ctrl(ctrl)

        print(f"执行动作：{self.q_path}")
        with self.arm.create_context(self.length) as ctx:
            for i in range(len(q)):
                ctrl.set_control(q[i], dq[i])
                time.sleep(0.001)
                if self.max_step and i >= self.max_step:
                    break
        self.finished.emit()