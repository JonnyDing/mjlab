import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv('/home/djw/Desktop/mjlab/src/motion_data/n1_csv/data_from_mocap/Dance_TK_60hz.csv')

# Extract column 20 (0-based index → 19)
joint_pos = df.iloc[:, 19].to_numpy()

# Compute velocity by numerical differentiation
joint_vel = joint_pos[1:] - joint_pos[:-1]

# For plotting, create step index (length = len(joint_vel))
steps = range(len(joint_vel))

# Plot
plt.figure(figsize=(8, 4))
plt.plot(steps, joint_vel)
plt.xlabel("Step")
plt.ylabel("Joint Velocity")
plt.title("Joint Velocity from Column 20")
plt.grid(True)

plt.show()
