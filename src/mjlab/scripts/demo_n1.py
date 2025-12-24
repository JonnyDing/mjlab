"""Script to run a tracking demo with a pretrained policy.

This demo downloads a pretrained checkpoint and motion file from cloud storage
and launches an interactive viewer with a humanoid robot performing a cartwheel.
"""

# from functools import partial

import tyro

from mjlab.scripts.play import PlayConfig, run_play

def main() -> None:
  """Run demo with pretrained tracking policy."""
  print("🎮 Setting up MJLab demo with pretrained tracking policy...")

  try:
    checkpoint_path = "logs/rsl_rl/n1_tracking/2025-12-22_17-10-17/model_8000.pt"
    motion_path = "/tmp/motion.npz"
    # print("checkpoint_path:",checkpoint_path)
    # print("motion_path:",motion_path)
  except RuntimeError as e:
    print(f"❌ Failed to download demo assets: {e}")
    print("Please check your internet connection and try again.")
    return

  args = tyro.cli(
    PlayConfig,
    default=PlayConfig(
      checkpoint_file=checkpoint_path,
      motion_file=motion_path,
      num_envs=8,
      viewer="viser",
      _demo_mode=True,
    ),
  )
  run_play("Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation", args)

if __name__ == "__main__":
  main()
