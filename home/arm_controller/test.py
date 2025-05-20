"""
Simple teaching demonstration. Teaches three joint positions
and connects them using motion generators. Also teaches a joint
trajectory that is then replayed.
"""
import sys
import time

import panda_py
import numpy as np
from panda_py import libfranka

from configs.config import ARM_URL
from src.logger.traj_logger import TrajectoryLogger
from src.replay.replay import Replay
from src.sampler.sampler import Sampler


def test_gripper():
    gripper = libfranka.Gripper(ARM_URL)
    gripper.move(0.07, 0.03)
    gripper.grasp(0.03, 0.03, 10)
    # gripper.move(0, 0.03)
    # output = gripper.read_once()
    # print(output.time)
    # print(output.width)
    # print(output.is_grasped)
    # print(output.max_width)
    # print(output.temperature)


if __name__ == '__main__':
    arm = panda_py.Panda(ARM_URL)
    # sample = Sampler(arm)
    # print(f"current pos: {sample.sample_pos()}")
    # data = sample.sample_trajectory()
    # traj_logger = TrajectoryLogger()
    # traj_logger.write(data, "data/traj", "trajectory")

    replay = Replay(arm)
    replay.replay_trajectory(path='data/traj/trajectory.h5')


def camera_test():
    import pyrealsense2 as rs
    pipe = rs.pipeline()
    profile = pipe.start()
    try:
      for i in range(0, 100):
        frames = pipe.wait_for_frames()
        for f in frames:
          print(f.profile)
    finally:
        pipe.stop()