from mjlab.tasks.registry import register_mjlab_task
from mjlab.tasks.velocity.rl import VelocityOnPolicyRunner

from .env_cfgs import fourier_n1_flat_env_cfg, fourier_n1_rough_env_cfg
from .rl_cfg import fourier_n1_ppo_runner_cfg

register_mjlab_task(
  task_id="Mjlab-Velocity-Rough-Fourier-N1",
  env_cfg=fourier_n1_rough_env_cfg(has_state_estimation=False),
  play_env_cfg=fourier_n1_rough_env_cfg(has_state_estimation=False,play=True),
  rl_cfg=fourier_n1_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Mjlab-Velocity-Flat-Fourier-N1",
  env_cfg=fourier_n1_flat_env_cfg(has_state_estimation=False),
  play_env_cfg=fourier_n1_flat_env_cfg(has_state_estimation=False,play=True),
  rl_cfg=fourier_n1_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)
