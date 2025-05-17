import os
import sys
from PyQt5.QtWidgets import QApplication
from controllers.arm_controller import ArmController
from src.controllers.camera import Camera
from src.controllers.hand_controller import HandController
from ui.control_panel import RobotControlUI
import panda_py
from panda_py import libfranka
from configs.config import *

# os.environ("QT_QPA_PLATFORM=offscreen")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    arm = ArmController(panda_py.Panda(ARM_URL))
    hand = HandController(libfranka.Gripper(ARM_URL))
    camera = Camera()
    # hand = HandController(hand_t.Client())

    ui = RobotControlUI(arm, hand, camera)
    ui.show()

    sys.exit(app.exec_())
