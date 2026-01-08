# Copyright (c) 2021-2024, The RSL-RL Project Developers.
# All rights reserved.
# Original code is licensed under the BSD-3-Clause license.
#
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# Copyright (c) 2025-2026, The Legged Lab Project Developers.
# All rights reserved.
#
# Copyright (c) 2025-2026, The TienKung-Lab Project Developers.
# All rights reserved.
# Modifications are licensed under the BSD-3-Clause license.
#
# This file contains code derived from the RSL-RL, Isaac Lab, and Legged Lab Projects,
# with additional modifications by the TienKung-Lab Project,
# and is distributed under the BSD-3-Clause license.

import argparse
import os
import sys
import time

import mujoco
import mujoco.viewer
import numpy as np
import torch
from pynput import keyboard
from scipy.spatial.transform import Rotation as R


class SimToSimCfg:
  """Configuration class for sim2sim parameters.

  Must be kept consistent with the training configuration.
  """

  class sim:
    sim_duration = 1000.0
    num_action = 21
    num_obs_per_step = 81
    actor_obs_history_length = 10
    dt = 0.005
    decimation = 4
    clip_observations = 100.0
    clip_actions = 100.0
    action_scale = 0.25

  class robot:
    gait_air_ratio_l: float = 0.6
    gait_air_ratio_r: float = 0.6
    gait_phase_offset_l: float = 0.6
    gait_phase_offset_r: float = 0.1
    gait_cycle: float = 0.5


class MujocoRunner:
  """
  Sim2Sim runner that loads a policy and a MuJoCo model
  to run real-time humanoid control simulation.

  Args:
      cfg (SimToSimCfg): Configuration object for simulation.
      policy_path (str): Path to the TorchScript exported policy.
      model_path (str): Path to the MuJoCo XML model.
  """

  def __init__(self, cfg: SimToSimCfg, policy_path, model_path):
    self.cfg = cfg
    network_path = policy_path
    self.model = mujoco.MjModel.from_xml_path(model_path)
    self.model.opt.timestep = self.cfg.sim.dt

    self.policy = torch.jit.load(network_path)
    self.data = mujoco.MjData(self.model)
    # self.viewer = mujoco_viewer.MujocoViewer(self.model, self.data)
    # self.viewer._render_every_frame = False
    self.count_lowlevel = 0
    self.init_variables()

  def init_variables(self) -> None:
    """Initialize simulation variables and joint index mappings."""
    self.dt = self.cfg.sim.decimation * self.cfg.sim.dt
    # self.dof_pos = np.zeros(self.cfg.sim.num_action)
    # self.dof_vel = np.zeros(self.cfg.sim.num_action)
    self.dof_pos = self.data.sensordata[0:21]
    self.dof_vel = self.data.sensordata[21:42]
    self.action = np.zeros(self.cfg.sim.num_action)
    self.target_dq = np.zeros(self.cfg.sim.num_action, dtype=np.double)
    self.default_dof_pos = np.array(
      [
        -0.2468,
        0.0,
        0.0,
        0.5181,
        0.0,
        -0.2468,
        -0.2468,
        0.0,
        0,
        0.5181,
        0.0,
        -0.2468,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
      ]
    )
    self.episode_length_buf = 0
    self.gait_phase = np.zeros(2)
    self.gait_cycle = self.cfg.robot.gait_cycle
    self.phase_ratio = np.array(
      [self.cfg.robot.gait_air_ratio_l, self.cfg.robot.gait_air_ratio_r]
    )
    self.phase_offset = np.array(
      [self.cfg.robot.gait_phase_offset_l, self.cfg.robot.gait_phase_offset_r]
    )

    # Initial command vel
    self.kp = np.array(
      [
        180,
        120,
        90,
        120,
        45,
        45,
        180,
        120,
        90,
        120,
        45,
        45,
        90,
        90,
        45,
        45,
        45,
        90,
        45,
        45,
        45,
      ],
      dtype=np.float32,
    )
    self.kd = np.array(
      [
        10,
        8,
        10,
        8,
        2.5,
        2.5,
        10,
        8,
        10,
        8,
        2.5,
        2.5,
        8,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
      ],
      dtype=np.float32,
    )
    self.command_vel = np.array([0.0, 0.0, 0.0])
    self.obs_history = np.zeros(
      (self.cfg.sim.num_obs_per_step * self.cfg.sim.actor_obs_history_length,),
      dtype=np.float32,
    )
    self.mujoco_to_isaac_idx = [
      0,  # left_thigh_pitch_link
      6,  # right_thigh_pitch_link
      12,  # waist_yaw_link
      1,  # left_thigh_roll_link
      7,  # right_thigh_roll_link
      13,  # left_upper_arm_pitch_link
      17,  # right_upper_arm_pitch_link
      2,  # left_thigh_yaw_link
      8,  # right_thigh_yaw_link
      14,  # left_upper_arm_roll_link
      18,  # right_upper_arm_roll_link
      3,  # left_shank_pitch_link
      9,  # right_shank_pitch_link
      15,  # left_upper_arm_yaw_link
      19,  # right_upper_arm_yaw_link
      4,  # left_foot_roll_link
      10,  # right_foot_roll_link
      16,  # left_lower_arm_pitch_link
      20,  # right_lower_arm_pitch_link
      5,  # left_foot_pitch_link
      11,  # right_foot_pitch_link
    ]
    self.isaac_to_mujoco_idx = [
      0,  # left_thigh_pitch_link
      3,  # left_thigh_roll_link
      7,  # left_thigh_yaw_link
      11,  # left_shank_pitch_link
      15,  # left_foot_roll_link
      19,  # left_foot_pitch_link
      1,  # right_thigh_pitch_link
      4,  # right_thigh_roll_link
      8,  # right_thigh_yaw_link
      12,  # right_shank_pitch_link
      16,  # right_foot_roll_link
      20,  # right_foot_pitch_link
      2,  # waist_yaw_link
      5,  # left_upper_arm_pitch_link
      9,  # left_upper_arm_roll_link
      13,  # left_upper_arm_yaw_link
      17,  # left_lower_arm_pitch_link
      6,  # right_upper_arm_pitch_link
      10,  # right_upper_arm_roll_link
      14,  # right_upper_arm_yaw_link
      18,  # right_lower_arm_pitch_link
    ]

  #   def get_obs(self) -> np.ndarray:
  # """
  # Compute current observation vector from MuJoCo sensors and internal state.

  # Returns:
  #     np.ndarray: Normalized and clipped observation history.
  # """

  # # Linear vel
  # obs[0:3] = self.data.sensor("imu_lin_vel").data.astype(np.double)

  # # Angular vel
  # obs[3:6] = self.data.sensor("angular-velocity").data.astype(np.double)

  # # Projected gravity
  # obs[6:9] = self.quat_rotate_inverse(
  #   self.data.sensor("angular-velocity").data[[1, 2, 3, 0]].astype(np.double),
  #   np.array([0, 0, -1]),
  # )
  # # Command velocity
  # obs[9:12] = self.command_vel

  # # Dof pos
  # obs[12 : 12 + self.cfg.sim.num_action] = self.dof_pos - self.default_dof_pos

  # # Dof vel
  # obs[12 + self.cfg.sim.num_action : 12 + 2 * self.cfg.sim.num_action] = self.dof_vel

  # # Action
  # obs[12 + 2 * self.cfg.sim.num_action : 12 + 3 * self.cfg.sim.num_action] = np.clip(
  #   self.action, -self.cfg.sim.clip_actions, self.cfg.sim.clip_actions
  # )

  # # Gait parameters
  # obs[12 + 3 * self.cfg.sim.num_action : 14 + 3 * self.cfg.sim.num_action] = np.sin(
  #   2 * np.pi * self.gait_phase
  # )
  # obs[14 + 3 * self.cfg.sim.num_action : 16 + 3 * self.cfg.sim.num_action] = np.cos(
  #   2 * np.pi * self.gait_phase
  # )
  # obs[16 + 3 * self.cfg.sim.num_action : 18 + 3 * self.cfg.sim.num_action] = (
  #   self.phase_ratio
  # )

  # # Update observation history
  # self.obs_history = np.roll(self.obs_history, shift=-self.cfg.sim.num_obs_per_step)
  # self.obs_history[-self.cfg.sim.num_obs_per_step :] = obs.copy()

  # return np.clip(
  #   self.obs_history, -self.cfg.sim.clip_observations, self.cfg.sim.clip_observations
  # )

  def pd_control(self, q, dq):
    """Calculates torques from position commands"""
    torques = (self.target_q - q) * self.kp + (self.target_dq - dq) * self.kd
    return torques

  def position_control(self) -> np.ndarray:
    """
    Apply position control using scaled action.

    Returns:
        np.ndarray: Target joint positions in MuJoCo order.
    """
    actions_scaled = self.action[self.isaac_to_mujoco_idx] * self.cfg.sim.action_scale
    return actions_scaled + self.default_dof_pos

  def get_imu_data(self) -> np.ndarray:
    q = self.data.qpos.astype(np.double)
    dq = self.data.qvel.astype(np.double)
    quat = (
      self.data.sensor("orientation").data[[1, 2, 3, 0]].astype(np.double)
    )  # x y z w
    omega = self.data.sensor("imu_ang_vel").data.astype(np.double)
    lin_vel = self.data.sensor("imu_lin_vel").data.astype(np.double)
    r = R.from_quat(quat)
    v = r.apply(self.data.qvel[:3], inverse=True).astype(np.double)  # In the base frame
    gvec = r.apply(np.array([0.0, 0.0, -1.0]), inverse=True).astype(np.double)

    return q, dq, quat, v, omega, gvec, lin_vel

  def run(self) -> None:
    """
    Run the simulation loop with keyboard-controlled commands.
    """
    with mujoco.viewer.launch_passive(self.model, self.data) as viewer:
      self.setup_keyboard_listener()
      self.listener.start()
      start = time.time()
      while viewer.is_running() and time.time() - start < self.cfg.sim.sim_duration:
        q, dq, quat, v, omega, gvec, lin_vel = self.get_imu_data()
        self.dof_pos = q[-self.cfg.sim.num_action :]
        self.dof_vel = dq[-self.cfg.sim.num_action :]
        step_start = time.time()
        if self.count_lowlevel % self.cfg.sim.decimation == 0:
          obs = np.zeros((self.cfg.sim.num_obs_per_step,), dtype=np.float32)
          obs[0:3] = lin_vel
          obs[3:6] = omega
          obs[6:9] = gvec
          obs[9:12] = self.command_vel
          print(self.command_vel)
          obs[12 : 12 + self.cfg.sim.num_action] = (
            self.dof_pos - self.default_dof_pos
          )[self.mujoco_to_isaac_idx]
          obs[12 + self.cfg.sim.num_action : 12 + 2 * self.cfg.sim.num_action] = (
            self.dof_vel[self.mujoco_to_isaac_idx]
          )
          obs[12 + 2 * self.cfg.sim.num_action : 12 + 3 * self.cfg.sim.num_action] = (
            self.action
          )
          obs[12 + 3 * self.cfg.sim.num_action : 14 + 3 * self.cfg.sim.num_action] = (
            np.sin(2 * np.pi * self.gait_phase)
          )
          obs[14 + 3 * self.cfg.sim.num_action : 16 + 3 * self.cfg.sim.num_action] = (
            np.cos(2 * np.pi * self.gait_phase)
          )
          obs[16 + 3 * self.cfg.sim.num_action : 18 + 3 * self.cfg.sim.num_action] = (
            self.phase_ratio
          )
          # Update observation history
          self.obs_history = np.roll(
            self.obs_history, shift=-self.cfg.sim.num_obs_per_step
          )
          self.obs_history[-self.cfg.sim.num_obs_per_step :] = obs.copy()

          # self.obs_history = self.get_obs()
          self.action[:] = (
            self.policy(torch.tensor(self.obs_history, dtype=torch.float32))
            .detach()
            .numpy()
          )
          self.action = np.clip(
            self.action, -self.cfg.sim.clip_actions, self.cfg.sim.clip_actions
          )

          self.target_q = (
            self.action[self.isaac_to_mujoco_idx] * self.cfg.sim.action_scale
            + self.default_dof_pos
          )

        # torque = self.pd_control(self.dof_pos, self.dof_vel)
        time_until_next_step = self.cfg.sim.dt - (time.time() - step_start)
        self.data.ctrl = self.position_control()
        mujoco.mj_step(self.model, self.data)
        viewer.sync()
        self.count_lowlevel += 1
        self.episode_length_buf += 1
        self.calculate_gait_para()
        if time_until_next_step > 0:
          time.sleep(time_until_next_step)
      self.listener.stop()
      # for sim_update in range(self.cfg.sim.decimation):
      #     step_start_time = time.time()
      #     # import ipdb; ipdb.set_trace()
      #     self.data.ctrl = self.pd_control(self.dof_pos, self.dof_vel)
      #     mujoco.mj_step(self.model, self.data)
      #     self.viewer.render()

      #     elapsed = time.time() - step_start_time
      #     sleep_time = self.cfg.sim.dt - elapsed
      #     if sleep_time > 0:
      #         time.sleep(sleep_time)
      # self.episode_length_buf += 1

      # self.listener.stop()
      # self.viewer.close()

  def quat_rotate_inverse(self, q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """
    Rotate a vector by the inverse of a quaternion.

    Args:
        q (np.ndarray): Quaternion (x, y, z, w) format.
        v (np.ndarray): Vector to rotate.

    Returns:
        np.ndarray: Rotated vector.
    """
    q_w = q[-1]
    q_vec = q[:3]
    a = v * (2.0 * q_w**2 - 1.0)
    b = np.cross(q_vec, v) * q_w * 2.0
    c = q_vec * np.dot(q_vec, v) * 2.0

    return a - b + c

  def calculate_gait_para(self) -> None:
    """
    Update gait phase parameters based on simulation time and offset.
    """
    t = self.episode_length_buf * self.dt / self.gait_cycle
    self.gait_phase[0] = (t + self.phase_offset[0]) % 1.0
    self.gait_phase[1] = (t + self.phase_offset[1]) % 1.0

  def adjust_command_vel(self, idx: int, increment: float) -> None:
    """
    Adjust command velocity vector.

    Args:
        idx (int): Index of velocity component (0=x, 1=y, 2=yaw).
        increment (float): Value to increment.
    """
    self.command_vel[idx] += increment
    self.command_vel[idx] = np.clip(self.command_vel[idx], -1.0, 1.0)  # vel clip

  def setup_keyboard_listener(self) -> None:
    """
    Set up keyboard event listener for user control input.
    """

    def on_press(key):
      try:
        if key.char == "8":  # NumPad 8      x += 0.2
          self.adjust_command_vel(0, 0.2)
        elif key.char == "2":  # NumPad 2      x -= 0.2
          self.adjust_command_vel(0, -0.2)
        elif key.char == "4":  # NumPad 4      y -= 0.2
          self.adjust_command_vel(1, -0.2)
        elif key.char == "6":  # NumPad 6      y += 0.2
          self.adjust_command_vel(1, 0.2)
        elif key.char == "7":  # NumPad 7      yaw += 0.2
          self.adjust_command_vel(2, -0.2)
        elif key.char == "9":  # NumPad 9      yaw -= 0.2
          self.adjust_command_vel(2, 0.2)
      except AttributeError:
        pass

    self.listener = keyboard.Listener(on_press=on_press)


if __name__ == "__main__":
  LEGGED_LAB_ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
  )
  parser = argparse.ArgumentParser(description="Run sim2sim Mujoco controller.")
  parser.add_argument(
    "--policy",
    type=str,
    default="/home/djw/Desktop/mjlab/Beyondmimic_Deploy_N1/fourier_n1_description/policy.pt",
    help="Path to policy.pt. If not specified, it will be set automatically based on --task",
  )
  parser.add_argument(
    "--model",
    type=str,
    default="/home/djw/Desktop/mjlab/Beyondmimic_Deploy_N1/fourier_n1_description/mjcf/n1.xml",
    help="Path to model.xml",
  )
  parser.add_argument(
    "--duration", type=float, default=100.0, help="Simulation duration in seconds"
  )
  args = parser.parse_args()

  if args.policy is None:
    args.policy = os.path.join(
      LEGGED_LAB_ROOT_DIR, "Exported_policy", f"{args.task}.pt"
    )

  if not os.path.isfile(args.policy):
    print(f"[ERROR] Policy file not found: {args.policy}")
    sys.exit(1)
  if not os.path.isfile(args.model):
    print(f"[ERROR] MuJoCo model file not found: {args.model}")
    sys.exit(1)

  print(f"[INFO] Loaded policy: {args.policy}")
  print(f"[INFO] Loaded model: {args.model}")

  sim_cfg = SimToSimCfg()
  sim_cfg.sim.sim_duration = args.duration

  runner = MujocoRunner(
    cfg=sim_cfg,
    policy_path=args.policy,
    model_path=args.model,
  )
  runner.run()
