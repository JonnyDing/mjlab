import gymnasium as gym

gym.register(
  id="Mjlab-Velocity-Rough-Fourier-N1",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.rough_env_cfg:FourierN1RoughEnvCfg",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:UnitreeG1PPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Velocity-Rough-Fourier-N1-Play",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.rough_env_cfg:FourierN1RoughEnvCfg_PLAY",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:FourierN1PPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Velocity-Flat-Fourier-N1",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:FourierN1FlatEnvCfg",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:FourierN1PPORunnerCfg",
  },
)

gym.register(
  id="Mjlab-Velocity-Flat-Fourier-N1-Play",
  entry_point="mjlab.envs:ManagerBasedRlEnv",
  disable_env_checker=True,
  kwargs={
    "env_cfg_entry_point": f"{__name__}.flat_env_cfg:FourierN1FlatEnvCfg_PLAY",
    "rl_cfg_entry_point": f"{__name__}.rl_cfg:FourierN1PPORunnerCfg",
  },
)
