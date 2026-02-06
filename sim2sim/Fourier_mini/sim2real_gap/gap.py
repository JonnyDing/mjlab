import math
import matplotlib
# 使用Agg后端，避免显示问题
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# 创建保存图像的目录
output_dir = "/home/djw/Desktop/mjlab/sim2sim/Fourier_mini/sim2real_gap/plots"
os.makedirs(output_dir, exist_ok=True)
print(f"图像保存目录: {output_dir}")

# 设置字体以避免问题
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 1. 读取 CSV ==========
sim_data = "/home/djw/Desktop/mjlab/log_data/tau_obs_combined.csv"
real_data = "/home/djw/Desktop/mjlab/sim2sim/Fourier_mini/sim2real_gap/kick.csv"
sim_df = pd.read_csv(sim_data)
real_df = pd.read_csv(real_data)
import ipdb; ipdb.set_trace()

# ======================
# 1️⃣ 定义列区间映射
# ======================
col_map = {
  "sim": {
    # sim数据：前21列是tau（不需要可视化），obs从第21列开始
    "motioninput": (21, 63),  # 42列: 21-62
    "anchor_ori": (63, 69),   # 6列: 63-68
    "ang": (69, 72),          # 3列: 69-71
    "qpos_offset": (72, 93),  # 21列: 72-92
    "qvel": (93, 114),        # 21列: 93-113
  },
  "real": {
    # real数据：前23列是tau（不需要可视化）
    "motioninput": (23, 65),  # 42列: 23-64
    "anchor_ori": (65, 71),   # 6列: 65-70
    "ang": (71, 74),          # 3列: 71-73
    "qpos_offset": (74, 95),  # 21列: 74-94
    "qvel": (95, 116),        # 21列: 95-115
  },
}


# ======================
# 2️⃣ 提取模块函数
# ======================
def extract_modules(df_sim, df_real, col_map):
  result = {}
  # 只可视化obs部分，不包含tau
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
# 3️⃣ 可视化模块（保存图像）
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

  plt.tight_layout()
  
  # 保存图像
  output_path = os.path.join(output_dir, f"{title}_comparison.png")
  plt.savefig(output_path, dpi=150, bbox_inches='tight')
  print(f"  已保存图像: {output_path}")
  
  # 打印统计信息
  print(f"  {title}统计: {num_dims}个维度")
  print(f"  Sim数据范围: [{np.min(data_sim):.3f}, {np.max(data_sim):.3f}]")
  print(f"  Real数据范围: [{np.min(data_real):.3f}, {np.max(data_real):.3f}]")
  mse = np.mean((data_sim - data_real) ** 2)
  print(f"  MSE: {mse:.6f}")
  
  plt.close(fig)  # 关闭图形以释放内存


# ======================
# 4️⃣ 主流程：提取 + 可视化 + 保存
# ======================
datasets = extract_modules(sim_df, real_df, col_map)

print("=" * 60)
print("Sim2Real Gap可视化 + 保存")
print("=" * 60)
print(f"图像保存目录: {output_dir}")
print("=" * 60)

for title, data_pair in datasets.items():
  print(f"\n处理模块: {title}")
  plot_category_comparison(data_pair["sim"], data_pair["real"], title)

print("\n" + "=" * 60)
print("处理完成")
print("=" * 60)

# 计算总体统计
print("\n总体统计:")
total_mse = 0
total_dims = 0
image_files = []
for title, data_pair in datasets.items():
  sim_data = data_pair["sim"]
  real_data = data_pair["real"]
  mse = np.mean((sim_data - real_data) ** 2)
  dims = sim_data.shape[1]
  total_mse += mse * dims
  total_dims += dims
  image_path = os.path.join(output_dir, f"{title}_comparison.png")
  image_files.append(image_path)
  print(f"  {title}: MSE={mse:.6f}, 维度={dims}, 图像={os.path.basename(image_path)}")

if total_dims > 0:
  overall_mse = total_mse / total_dims
  print(f"\n加权平均MSE: {overall_mse:.6f} (基于{total_dims}个维度)")

print(f"\n生成的图像文件:")
for img_file in image_files:
  if os.path.exists(img_file):
    file_size = os.path.getsize(img_file) / 1024  # KB
    print(f"  {os.path.basename(img_file)} ({file_size:.1f} KB)")
  else:
    print(f"  {os.path.basename(img_file)} (未找到)")

print("=" * 60)
