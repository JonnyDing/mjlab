import json
import numpy as np
import pandas as pd

# 读取JSON文件
json_path = "/home/djw/Desktop/mjlab/src/motion_data/n1_json/Dance_Olypic.json"
with open(json_path, 'r') as f:
    data = json.load(f)

# 获取Frames数据
frames = np.array(data["Frames"])

# 提取各部分
root_pos = frames[4650:, :3]          # 根节点位置
quat = frames[4650:, 3:7]            # 四元数 (x, y, z, w)
dof_full = frames[4650:, 13:36]       # 完整的dof_pos

# 删除第29列和第24列（对应索引28和23）
# 在dof_full中，对应索引21和16
cols_to_keep = [i for i in range(23) if i not in [17, 22]]
dof_filtered = dof_full[:, cols_to_keep]

# 合并数据
combined = np.concatenate([root_pos, quat, dof_filtered], axis=1)

# 保存为CSV
output_path = "/home/djw/Desktop/mjlab/src/motion_data/n1_json/Dance_Olypic_processed_6200.csv"
pd.DataFrame(combined).to_csv(output_path, header=False, index=False)

print(f"处理完成！保存到: {output_path}")
print(f"数据形状: {combined.shape}")
