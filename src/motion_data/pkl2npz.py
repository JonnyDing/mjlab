# def pkl_to_npz(pkl_path, npz_path):
#   # 读取 PKL 文件
#   with open(pkl_path, "rb") as f:
#     data = joblib.load(pkl_path)

#   # 检查数据类型并相应处理
#   if isinstance(data, dict):
#     # 如果是字典，将每个键值对保存到 NPZ
#     np.savez(npz_path, **data)
#     print(f"转换完成！PKL 中的键: {list(data.keys())}")
#   elif isinstance(data, (np.ndarray, list)):
#     # 如果是数组或列表，保存为 'data' 键
#     np.savez(npz_path, data=data)
#     print("转换完成！数据保存为 'data' 键")
#   else:
#     # 其他数据类型
#     np.savez(npz_path, data=data)
#     print(f"转换完成！数据类型: {type(data)}")

#   return data


# # 使用示例
# pkl_to_npz("dance.pkl", "dance.npz")
