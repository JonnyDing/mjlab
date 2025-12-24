import pickle
import numpy as np
import pandas as pd

# 1. 读取文件
input_path = "/home/djw/Desktop/mocap/motion_data/g1/g1_pkl/jump_degree_level5.pkl"  # 你可以换成自己的路径
with open(input_path, "rb") as f:
  data = pickle.load(f)
# data = next(iter(data.values()))
# 2. 提取三个关键字段
root_trans = np.array(data["root_pos"])
root_rot = np.array(data["root_rot"])
dof = np.array(data["dof_pos"])

# 3. 沿最后一个维度拼接
merged = np.concatenate([root_trans, root_rot, dof], axis=-1)

# === 保存为 CSV ===
output_path = (
  "/home/djw/Desktop/mocap/motion_data/g1/g1_csv/jump_degree_level5.csv"
)
pd.DataFrame(merged).to_csv(output_path, header=False, index=False)

print(f"✅ 已保存为: {output_path}")
