"""Unitree G1 constants."""

from pathlib import Path

import mujoco

from mjlab import MJLAB_SRC_PATH
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.actuator import (
  ElectricActuator,
)
from mjlab.utils.os import update_assets
from mjlab.utils.spec_config import ActuatorCfg, CollisionCfg

##
# MJCF and assets.
##
"""
            <!-- joint -->
            <default class="joint_8029E">
                <joint armature="0.12109824" type="hinge" range="0 0" actuatorfrcrange="-95 95"/>
            </default>
            <default class="joint_6043E">
                <joint armature="0.167592" type="hinge" range="0 0" actuatorfrcrange="-54 54"/>
            </default>
            <default class="joint_4530E">
                <joint armature="0.0312822" type="hinge" range="0 0" actuatorfrcrange="-30 30"/>
            </default>

            <!-- motor -->
            <default class="motor_8029E">
                <motor ctrllimited="true" ctrlrange="-95 95"/>
            </default>
            <default class="motor_6043E">
                <motor ctrllimited="true" ctrlrange="-54 54"/>
            </default>
            <default class="motor_4530E">
                <motor ctrllimited="true" ctrlrange="-30 30"/>
            </default>

"""
N1_XML: Path = (
  MJLAB_SRC_PATH / "asset_zoo" / "robots" / "fourier_n1" / "xmls" / "n1.xml"
)
assert N1_XML.exists()


def get_assets(meshdir: str) -> dict[str, bytes]:
  assets: dict[str, bytes] = {}
  update_assets(assets, N1_XML.parent / "assets", meshdir)
  return assets


def get_spec() -> mujoco.MjSpec:
  spec = mujoco.MjSpec.from_file(str(N1_XML))
  spec.assets = get_assets(spec.meshdir)
  return spec


##
# Actuator config.
##

# Motor specs
ARMATURE_8029E = 0.12109824
ARMATURE_6043E = 0.167592
ARMATURE_4530E = 0.0312822

# hip_pitch knee_pitch
ACTUATOR_8029E = ElectricActuator(
  reflected_inertia=ARMATURE_8029E,
  velocity_limit=12.356,
  effort_limit=95.0,
)
# hip_roll hip_yaw waist_yaw shoulder_pitch
ACTUATOR_6043E = ElectricActuator(
  reflected_inertia=ARMATURE_6043E,
  velocity_limit=14.738,
  effort_limit=54.0,
)

ACTUATOR_4530E = ElectricActuator(
  reflected_inertia=ARMATURE_4530E,
  velocity_limit=16.747,
  effort_limit=30.0,
)
FN_BY_GROUP = {
  "8029E": (5.0, 1.5),  # hip_pitch, knee_pitch
  "6043E": (5.0, 0.9),  # hip_roll, hip_yaw, waist_yaw, shoulder_pitch
  "4530E": (5.0, 0.9),  # ankles, shoulder_roll/yaw, elbow_pitch
}

NATURAL_FREQ_8029E = FN_BY_GROUP["8029E"][0] * 2.0 * 3.1415926535  # 10Hz
DAMPING_RATIO_8029E = FN_BY_GROUP["8029E"][1]

NATURAL_FREQ_6043E = FN_BY_GROUP["6043E"][0] * 2.0 * 3.1415926535  # 10Hz
DAMPING_RATIO_6043E = FN_BY_GROUP["6043E"][1]

NATURAL_FREQ_4530E = FN_BY_GROUP["4530E"][0] * 2.0 * 3.1415926535  # 10Hz
DAMPING_RATIO_4530E = FN_BY_GROUP["4530E"][1]

STIFFNESS_8029E = ARMATURE_8029E * NATURAL_FREQ_8029E**2
STIFFNESS_6043E = ARMATURE_6043E * NATURAL_FREQ_6043E**2
STIFFNESS_4530E = ARMATURE_4530E * NATURAL_FREQ_4530E**2

DAMPING_8029E = 2.0 * DAMPING_RATIO_8029E * ARMATURE_8029E * NATURAL_FREQ_8029E
DAMPING_6043E = 2.0 * DAMPING_RATIO_6043E * ARMATURE_6043E * NATURAL_FREQ_6043E
DAMPING_4530E = 2.0 * DAMPING_RATIO_4530E * ARMATURE_4530E * NATURAL_FREQ_4530E

N1_ACTUATOR_8029E = ActuatorCfg(
  joint_names_expr=[
    ".*_hip_pitch_joint",
    ".*_knee_pitch_joint",
    ".*_shoulder_pitch_joint",
  ],
  effort_limit=ACTUATOR_8029E.effort_limit,
  armature=ACTUATOR_8029E.reflected_inertia,
  stiffness=STIFFNESS_8029E,
  damping=DAMPING_8029E,
)

N1_ACTUATOR_6043E = ActuatorCfg(
  joint_names_expr=[
    ".*_hip_roll_joint",
    ".*_hip_yaw_joint",
    "waist_yaw_joint",
  ],
  effort_limit=ACTUATOR_6043E.effort_limit,
  armature=ACTUATOR_6043E.reflected_inertia,
  stiffness=STIFFNESS_6043E,
  damping=DAMPING_6043E,
)
N1_ACTUATOR_4530E = ActuatorCfg(
  joint_names_expr=[
    ".*_ankle_roll_joint",
    ".*_ankle_pitch_joint",
    ".*_shoulder_roll_joint",
    ".*_shoulder_yaw_joint",
    ".*_elbow_pitch_joint",
  ],
  effort_limit=ACTUATOR_4530E.effort_limit,
  armature=ACTUATOR_4530E.reflected_inertia,
  stiffness=STIFFNESS_4530E,
  damping=DAMPING_4530E,
)


##
# Keyframe config.
##

HOME_KEYFRAME = EntityCfg.InitialStateCfg(
  pos=(0, 0, 0.686),
  joint_pos={
    ".*_hip_pitch_joint": -0.2468,
    ".*_knee_pitch_joint": 0.5181,
    ".*_ankle_pitch_joint": -0.2468,
  },
  joint_vel={".*": 0.0},
)

KNEES_BENT_KEYFRAME = EntityCfg.InitialStateCfg(
  pos=(0, 0, 0.686),
  joint_pos={
    ".*_hip_pitch_joint": -0.2468,
    ".*_knee_pitch_joint": 0.5181,
    ".*_ankle_pitch_joint": -0.2468,
  },
  joint_vel={".*": 0.0},
)

##
# Collision config.
##

# This enables all collisions, including self collisions.
# Self-collisions are given condim=1 while foot collisions
# are given condim=3 and custom friction and solimp.
FULL_COLLISION = CollisionCfg(
  geom_names_expr=[".*_collision"],
  condim={r"^(left|right)_foot[1-7]_collision$": 3, ".*_collision": 1},
  priority={r"^(left|right)_foot[1-7]_collision$": 1},
  friction={r"^(left|right)_foot[1-7]_collision$": (0.6,)},
)

FULL_COLLISION_WITHOUT_SELF = CollisionCfg(
  geom_names_expr=[".*_collision"],
  contype=0,
  conaffinity=1,
  condim={r"^(left|right)_foot[1-7]_collision$": 3, ".*_collision": 1},
  priority={r"^(left|right)_foot[1-7]_collision$": 1},
  friction={r"^(left|right)_foot[1-7]_collision$": (0.6,)},
)

# This disables all collisions except the feet.
# Feet get condim=3, all other geoms are disabled.
FEET_ONLY_COLLISION = CollisionCfg(
  geom_names_expr=[r"^(left|right)_foot[1-7]_collision$"],
  contype=0,
  conaffinity=1,
  condim=3,
  priority=1,
  friction=(0.6,),
)

##
# Final config.
##

N1_ARTICULATION = EntityArticulationInfoCfg(
  actuators=(
    N1_ACTUATOR_8029E,
    N1_ACTUATOR_6043E,
    N1_ACTUATOR_4530E,
  ),
  soft_joint_pos_limit_factor=0.9,
)

N1_ROBOT_CFG = EntityCfg(
  init_state=KNEES_BENT_KEYFRAME,
  collisions=(FULL_COLLISION,),
  spec_fn=get_spec,
  articulation=N1_ARTICULATION,
)

N1_ACTION_SCALE: dict[str, float] = {}
for a in N1_ARTICULATION.actuators:
  e = a.effort_limit
  s = a.stiffness
  names = a.joint_names_expr
  if not isinstance(e, dict):
    e = {n: e for n in names}
  if not isinstance(s, dict):
    s = {n: s for n in names}
  for n in names:
    if n in e and n in s and s[n]:
      N1_ACTION_SCALE[n] = 0.8 * e[n] / s[n]
print(N1_ACTION_SCALE)
print("....")
if __name__ == "__main__":
  import mujoco.viewer as viewer

  from mjlab.entity.entity import Entity

  robot = Entity(N1_ROBOT_CFG)

  viewer.launch(robot.spec.compile())
