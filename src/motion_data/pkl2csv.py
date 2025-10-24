import joblib
import numpy as np
import pandas as pd

# 1. 读取文件
input_path = "/home/djw/Desktop/mjlab/src/motion_data/video_CR7_level2_filter_amass_cont_mask_fixed_inter0.5_S30-30_E133-30.pkl"  # 你可以换成自己的路径
data = joblib.load(input_path)
data = next(iter(data.values()))
# 2. 提取三个关键字段
root_trans = np.array(data["root_trans_offset"])
root_rot = np.array(data["root_rot"])
dof = np.array(data["dof"])

# 3. 沿最后一个维度拼接
merged = np.concatenate([root_trans, root_rot, dof], axis=-1)

# === 保存为 CSV ===
output_path = "//home/djw/Desktop/mjlab/src/motion_data/CR7.csv"
pd.DataFrame(merged).to_csv(output_path, header=False, index=False)

print(f"✅ 已保存为: {output_path}")
