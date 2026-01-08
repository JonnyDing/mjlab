import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("/home/djw/Desktop/mjlab/log_data/hip_joint_pos.csv")

# 设置绘图风格
# plt.style.use('seaborn-darkgrid')
plt.figure(figsize=(12, 6))

# 遍历每一列（除 timestep）
for col in df.columns[1:]:
  plt.plot(df["timestep"], df[col], label=col)

  # 输出最大值和最小值
  max_val = df[col].max()
  min_val = df[col].min()
  print(
    f"{col}:最大期望关节位置 = {max_val:.4f} rad, 最小期望关节位置 = {min_val:.4f} rad"
  )

# 图形标题与标签
plt.title("Hip Joint Angles Over Time", fontsize=16)
plt.xlabel("Timestep", fontsize=14)
plt.ylabel("Angle (rad)", fontsize=14)
plt.legend()
plt.tight_layout()
plt.show()
