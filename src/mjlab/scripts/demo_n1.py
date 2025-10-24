"""Script to run a tracking demo with a pretrained policy.

This demo downloads a pretrained checkpoint and motion file from cloud storage
and launches an interactive viewer with a humanoid robot performing a cartwheel.
"""

from functools import partial

import tyro

from mjlab.scripts.play import run_play


def main() -> None:
  """Run demo with pretrained tracking policy."""
  print("🎮 Setting up MJLab demo with pretrained tracking policy...")

  try:
    checkpoint_path = "/logs/rsl_rl/n1_tracking/CR7_std_0.3/model_3500.pt"
    motion_path = "/tmp/motion.npz"
    # print("checkpoint_path:",checkpoint_path)
    # print("motion_path:",motion_path)
  except RuntimeError as e:
    print(f"❌ Failed to download demo assets: {e}")
    print("Please check your internet connection and try again.")
    return

  tyro.cli(
    partial(
      run_play,
      task="Mjlab-Tracking-Flat-Fourier-N1-No-State-Estimation-Play",
      checkpoint_file=checkpoint_path,
      motion_file=motion_path,
      num_envs=8 * 2,
      render_all_envs=True,
      viewer="viser",
    )
  )


if __name__ == "__main__":
  main()
