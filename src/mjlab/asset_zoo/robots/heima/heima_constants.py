"""Heima robot constants."""

from pathlib import Path

import mujoco

from mjlab import MJLAB_SRC_PATH
from mjlab.actuator import BuiltinPositionActuatorCfg
from mjlab.entity import EntityArticulationInfoCfg, EntityCfg
from mjlab.utils.os import update_assets
from mjlab.utils.spec_config import CollisionCfg

##
# MJCF and assets.
##

HEIMA_XML: Path = (
  MJLAB_SRC_PATH / "asset_zoo" / "robots" / "heima" / "xmls" / "heima.xml"
)
assert HEIMA_XML.exists()


def get_assets(meshdir: str) -> dict[str, bytes]:
  assets: dict[str, bytes] = {}
  update_assets(assets, HEIMA_XML.parent / "assets", meshdir)
  return assets


def get_spec() -> mujoco.MjSpec:
  spec = mujoco.MjSpec.from_file(str(HEIMA_XML))
  spec.assets = get_assets(spec.meshdir)
  return spec


##
# Actuator config.
##

# Motor specifications:
# - X12: Gear ratio 20, used for hip_roll, hip_yaw, knee_pitch
# - X15: Gear ratio 20.25, used for hip_pitch
# - X6: Gear ratio 19.61, used for ankle_pitch, ankle_roll (parallel configuration)

# Natural frequency and damping ratio (similar to G1)
NATURAL_FREQ = 10 * 2.0 * 3.1415926535  # 10Hz
DAMPING_RATIO = 2.0

# Armature values estimated based on gear ratios and typical motor characteristics
# These values can be tuned based on real hardware testing
ARMATURE_X6 = 0.005    # Small motor for ankle joints
ARMATURE_X12 = 0.030   # Medium motor for hip roll/yaw and knee
ARMATURE_X15 = 0.050   # Larger motor for hip pitch

# Compute stiffness: k = I * ω_n²
STIFFNESS_X6 = ARMATURE_X6 * NATURAL_FREQ**2
STIFFNESS_X12 = ARMATURE_X12 * NATURAL_FREQ**2
STIFFNESS_X15 = ARMATURE_X15 * NATURAL_FREQ**2

# Compute damping: c = 2 * ζ * I * ω_n
DAMPING_X6 = 2.0 * DAMPING_RATIO * ARMATURE_X6 * NATURAL_FREQ
DAMPING_X12 = 2.0 * DAMPING_RATIO * ARMATURE_X12 * NATURAL_FREQ
DAMPING_X15 = 2.0 * DAMPING_RATIO * ARMATURE_X15 * NATURAL_FREQ

# X12 actuator: hip_roll, hip_yaw, knee_pitch (320 Nm)
HEIMA_ACTUATOR_X12 = BuiltinPositionActuatorCfg(
  target_names_expr=(
    "J_hip_r_roll",
    "J_hip_l_roll",
    "J_hip_r_yaw",
    "J_hip_l_yaw",
    "J_knee_r_pitch",
    "J_knee_l_pitch",
  ),
  stiffness=STIFFNESS_X12,
  damping=DAMPING_X12,
  effort_limit=272.0,
  armature=ARMATURE_X12,
)

# X15 actuator: hip_pitch (450 Nm)
HEIMA_ACTUATOR_X15 = BuiltinPositionActuatorCfg(
  target_names_expr=(
    "J_hip_r_pitch",
    "J_hip_l_pitch",
  ),
  stiffness=STIFFNESS_X15,
  damping=DAMPING_X15,
  effort_limit=382.5,
  armature=ARMATURE_X15,
)

# X6 actuator (parallel configuration): ankle_pitch, ankle_roll (60 Nm each, 120 Nm total)
# Similar to G1, ankles use parallel configuration with 2 X6 actuators
# Therefore, stiffness, damping, effort_limit, and armature are doubled
HEIMA_ACTUATOR_ANKLE = BuiltinPositionActuatorCfg(
  target_names_expr=(
    "J_ankle_r_pitch",
    "J_ankle_l_pitch",
    "J_ankle_r_roll",
    "J_ankle_l_roll",
  ),
  stiffness=STIFFNESS_X6 * 2,
  damping=DAMPING_X6 * 2,
  effort_limit=48.0 * 2,  # 2 motors in parallel
  armature=ARMATURE_X6 * 2,
)
import ipdb;ipdb.set_trace()
##
# Keyframe config.
##

HOME_KEYFRAME = EntityCfg.InitialStateCfg(
  pos=(0, 0, 1.09),
  joint_pos={
    "J_hip_r_pitch": 0.4,
    "J_hip_l_pitch": 0.4,
    "J_knee_r_pitch": -0.8,
    "J_knee_l_pitch": -0.8,
    "J_ankle_r_pitch": 0.4,
    "J_ankle_l_pitch": 0.4,
  },
  joint_vel={".*": 0.0},
)

##
# Collision config.
##

# Enable all collisions including self-collisions
# Foot collisions use condim=3, self-collisions use condim=1
FULL_COLLISION = CollisionCfg(
  geom_names_expr=(".*_collision",),
  condim={r"^(left|right)_foot[1-7]_collision$": 3, ".*_collision": 1},
  priority={r"^(left|right)_foot[1-7]_collision$": 1},
  friction={r"^(left|right)_foot[1-7]_collision$": (0.8,)},
)

FULL_COLLISION_WITHOUT_SELF = CollisionCfg(
  geom_names_expr=(".*_collision",),
  contype=0,
  conaffinity=1,
  condim={r"^(left|right)_foot[1-7]_collision$": 3, ".*_collision": 1},
  priority={r"^(left|right)_foot[1-7]_collision$": 1},
  friction={r"^(left|right)_foot[1-7]_collision$": (0.8,)},
)

# Feet only collision
FEET_ONLY_COLLISION = CollisionCfg(
  geom_names_expr=(r"^(left|right)_foot[1-7]_collision$",),
  contype=0,
  conaffinity=1,
  condim=3,
  priority=1,
  friction=(0.8,),
)

##
# Final config.
##

HEIMA_ARTICULATION = EntityArticulationInfoCfg(
  actuators=(
    HEIMA_ACTUATOR_X12,
    HEIMA_ACTUATOR_X15,
    HEIMA_ACTUATOR_ANKLE,
  ),
  soft_joint_pos_limit_factor=0.9,
)


def get_heima_robot_cfg() -> EntityCfg:
  """Get a fresh Heima robot configuration instance.

  Returns a new EntityCfg instance each time to avoid mutation issues when
  the config is shared across multiple places.
  """
  
  return EntityCfg(
    init_state=HOME_KEYFRAME,
    collisions=(FULL_COLLISION,),
    spec_fn=get_spec,
    articulation=HEIMA_ARTICULATION,
  )


HEIMA_ACTION_SCALE: dict[str, float] = {}
for a in HEIMA_ARTICULATION.actuators:
  assert isinstance(a, BuiltinPositionActuatorCfg)
  e = a.effort_limit
  s = a.stiffness
  names = a.target_names_expr
  assert e is not None
  for n in names:
    HEIMA_ACTION_SCALE[n] = 0.25 * e / s
    print(f"Actuator with target_names_expr={names} has action scale {0.25 * e / s:.4f}")

if __name__ == "__main__":
  import mujoco.viewer as viewer

  from mjlab.entity.entity import Entity

  robot = Entity(get_heima_robot_cfg())

  viewer.launch(robot.spec.compile())



