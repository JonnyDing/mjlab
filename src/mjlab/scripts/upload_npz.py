import wandb
from loguru import logger

REGISTRY_NAME = "motions"
COLLECTION_NAME = "motion"

run = wandb.init(project="csv_to_npz", name=COLLECTION_NAME, entity="ding268452")
logged_artifact = run.log_artifact(
  artifact_or_path="/home/djw/Desktop/mjlab/src/motion_data/dance.npz",
  name=COLLECTION_NAME,
  type=REGISTRY_NAME,
)
current_username = wandb.api.viewer().get("username")
logger.info(f"<red>[INFO]: Using WandB username: {current_username}</red>")
run.link_artifact(
  artifact=logged_artifact,
  target_path=f"{current_username}/{REGISTRY_NAME}/{COLLECTION_NAME}",
)
# run.link_artifact(artifact=logged_artifact, target_path=f"wandb-registry-{REGISTRY_NAME}/{COLLECTION_NAME}")
