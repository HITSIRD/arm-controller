import os
import sys
from PyQt5.QtWidgets import QApplication
from controllers.arm_controller import ArmController


from home.arm_controller.configs.config import ARM_URL
from home.arm_controller.src.controllers.camera import Camera
from home.arm_controller.src.controllers.hand_controller import HandController
from ui.control_panel import RobotControlUI
import panda_py
from panda_py import libfranka


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
