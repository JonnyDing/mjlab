import math
import matplotlib
matplotlib.use("Agg")  # 禁用 TkAgg，避免图标加载错误

import matplotlib.pyplot as plt
import pandas as pd

# ========== 1. 读取 CSV ==========
sim_data = "/home/djw/Desktop/mjlab/log_data/motion_data_log.csv"
real_data = "/home/djw/Desktop/mjlab/Beyondmimic_Deploy_N1/fourier_n1_description/sim2real_gap/2025-11-13-171320.csv"
sim_df = pd.read_csv(sim_data)
real_df = pd.read_csv(real_data)


# ======================
# 1️⃣ 定义列区间映射
# ======================
col_map = {
  "sim": {
    "motioninput": (1, 43),
    "anchor_ori": (43, 49),
    "ang": (49, 52),
    "qpos_offset": (52, 73),
    "qvel": (73, 94),
    # "tau": (94, 115)
  },
  "real": {
    "motioninput": (23, 65),
    "anchor_ori": (65, 71),
    "ang": (71, 74),
    "qpos_offset": (74, 95),
    "qvel": (95, 116),
    # "tau": (0, 22)
  },
}


# ======================
# 2️⃣ 提取模块函数
# ======================
def extract_modules(df_sim, df_real, col_map):
  result = {}
  for key in ["motioninput", "anchor_ori", "ang", "qpos_offset", "qvel"]:
    sim_start, sim_end = col_map["sim"][key]
    real_start, real_end = col_map["real"][key]

    sim_data = df_sim.iloc[:237, sim_start:sim_end].to_numpy()
    real_data = df_real.iloc[:237, real_start:real_end].to_numpy()

    # 自动对齐列数（防止不同步）
    n = min(sim_data.shape[1], real_data.shape[1])
    sim_data, real_data = sim_data[:, :n], real_data[:, :n]

    result[key] = {"sim": sim_data, "real": real_data}
  return result


# ======================
# 3️⃣ 绘图模块
# ======================
def plot_category_comparison(data_sim, data_real, title):
  num_dims = data_sim.shape[1]
  num_rows = int(math.ceil(math.sqrt(num_dims)))
  num_cols = int(math.ceil(num_dims / num_rows))

  fig, axes = plt.subplots(num_rows, num_cols, figsize=(num_cols * 2.3, num_rows * 1.8))
  fig.suptitle(f"{title} Comparison", fontsize=12, y=1.02)
  axes = axes.flatten()

  for i in range(num_dims):
    axes[i].plot(data_sim[:, i], "b-", linewidth=0.8, label="Sim")
    axes[i].plot(data_real[:, i], "r--", linewidth=0.8, label="Real")
    axes[i].set_title(f"{title}_{i}", fontsize=8)
    axes[i].grid(True)
    if i == 0:
      axes[i].legend(fontsize=7)

  # 去掉空子图
  for j in range(num_dims, len(axes)):
    axes[j].axis("off")

  # plt.tight_layout()
  plt.show()


# ======================
# 4️⃣ 主流程：提取 + 可视化
# ======================
datasets = extract_modules(sim_df, real_df, col_map)

for title, data_pair in datasets.items():
  print(f"正在绘制模块: {title}")
  plot_category_comparison(data_pair["sim"], data_pair["real"], title)
