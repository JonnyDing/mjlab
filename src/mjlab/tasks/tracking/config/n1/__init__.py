from mjlab.tasks.registry import register_mjlab_task
from mjlab.tasks.tracking.rl import MotionTrackingOnPolicyRunner

from .env_cfgs import fourier_n1_flat_tracking_env_cfg
from .rl_cfg import fourier_n1_tracking_ppo_runner_cfg

register_mjlab_task(
  task_id="Mjlab-Tracking-Flat-Fourier-N1",
  env_cfg=fourier_n1_flat_tracking_env_cfg(),
  play_env_cfg=fourier_n1_flat_tracking_env_cfg(play=True),
  rl_cfg=fourier_n1_tracking_ppo_runner_cfg(),
  runner_cls=MotionTrackingOnPolicyRunner,
)

register_mjlab_task(
  task_id="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation",
  env_cfg=fourier_n1_flat_tracking_env_cfg(has_state_estimation=False),
  play_env_cfg=fourier_n1_flat_tracking_env_cfg(has_state_estimation=False, play=True),
  rl_cfg=fourier_n1_tracking_ppo_runner_cfg(),
  runner_cls=MotionTrackingOnPolicyRunner,
)


# gym.register(
#   id="Mjlab-Tracking-Flat-Fourier-N1",
#   entry_point="mjlab.envs:ManagerBasedRlEnv",
#   disable_env_checker=True,
#   kwargs={
#     "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatEnvCfg",
#     "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
#   },
# )

# gym.register(
#   id="Mjlab-Tracking-Flat-Fourier-N1-Play",
#   entry_point="mjlab.envs:ManagerBasedRlEnv",
#   disable_env_checker=True,
#   kwargs={
#     "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatEnvCfg_PLAY",
#     "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
#   },
# )

# gym.register(
#   id="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation",
#   entry_point="mjlab.envs:ManagerBasedRlEnv",
#   disable_env_checker=True,
#   kwargs={
#     "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatNoStateEstimationEnvCfg",
#     "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
#   },
# )

# gym.register(
#   id="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation-Play",
#   entry_point="mjlab.envs:ManagerBasedRlEnv",
#   disable_env_checker=True,
#   kwargs={
#     "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatNoStateEstimationEnvCfg_PLAY",
#     "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
#   },
# )
