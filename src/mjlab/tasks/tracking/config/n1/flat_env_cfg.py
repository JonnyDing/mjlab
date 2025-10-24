from dataclasses import dataclass, replace

from mjlab.asset_zoo.robots.fourier_n1.n1_constants import N1_ACTION_SCALE, N1_ROBOT_CFG
from mjlab.tasks.tracking.tracking_env_cfg import TrackingEnvCfg
from mjlab.utils.spec_config import ContactSensorCfg


@dataclass
class N1FlatEnvCfg(TrackingEnvCfg):
  def __post_init__(self):
    self_collision_sensor = ContactSensorCfg(
      name="self_collision",
      subtree1="base_link",
      subtree2="base_link",
      data=("found",),
      reduce="netforce",
      num=10,  # Report up to 10 contacts.
    )
    n1_cfg = replace(N1_ROBOT_CFG, sensors=(self_collision_sensor,))

    self.scene.entities = {"robot": n1_cfg}
    self.actions.joint_pos.scale = N1_ACTION_SCALE

    self.commands.motion.anchor_body_name = "waist_yaw_link"
    self.commands.motion.body_names = [
      "base_link",
      "left_thigh_roll_link",
      "left_shank_pitch_link",
      "left_foot_pitch_link",
      "right_thigh_roll_link",
      "right_shank_pitch_link",
      "right_foot_pitch_link",
      "waist_yaw_link",
      "left_upper_arm_roll_link",
      "left_lower_arm_pitch_link",
      "right_upper_arm_roll_link",
      "right_lower_arm_pitch_link",
    ]

    self.events.foot_friction.params["asset_cfg"].geom_names = [
      r"^(left|right)_foot[1-7]_collision$"
    ]
    self.events.base_com.params["asset_cfg"].body_names = "torso_link"

    self.terminations.ee_body_pos.params["body_names"] = [
      "left_foot_pitch_link",
      "right_foot_pitch_link",
      "left_lower_arm_pitch_link",
      "right_lower_arm_pitch_link",
    ]

    self.viewer.body_name = "waist_yaw_link"


@dataclass
class N1FlatNoStateEstimationEnvCfg(N1FlatEnvCfg):
  def __post_init__(self):
    super().__post_init__()

    self.observations.policy.motion_anchor_pos_b = None
    self.observations.policy.base_lin_vel = None


@dataclass
class N1FlatEnvCfg_PLAY(N1FlatEnvCfg):
  def __post_init__(self):
    super().__post_init__()

    self.observations.policy.enable_corruption = False
    self.events.push_robot = None

    # Disable RSI randomization.
    self.commands.motion.pose_range = {}
    self.commands.motion.velocity_range = {}

    # Effectively infinite episode length.
    self.episode_length_s = int(1e9)


@dataclass
class N1FlatNoStateEstimationEnvCfg_PLAY(N1FlatNoStateEstimationEnvCfg):
  def __post_init__(self):
    super().__post_init__()

    self.observations.policy.enable_corruption = False
    self.events.push_robot = None

    # Disable RSI randomization.
    self.commands.motion.pose_range = {}
    self.commands.motion.velocity_range = {}

    # Effectively infinite episode length.
    self.episode_length_s = int(1e9)
