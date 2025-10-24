import gymnasium as gym

gym.register(
  id="Mjlab-Tracking-Flat-Fourier-N1",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatEnvCfg",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Tracking-Flat-Fourier-N1-Play",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatEnvCfg_PLAY",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatNoStateEstimationEnvCfg",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation-Play",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:N1FlatNoStateEstimationEnvCfg_PLAY",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:N1FlatPPORunnerCfg",
  },
)
