import mujoco
import numpy as np


class FootFrictionEstimator:
  def __init__(self, model, data, left_foot_geoms, right_foot_geoms, floor_geom_id):
    self.model = model
    self.data = data
    self.left_foot_geoms = set(left_foot_geoms)
    self.right_foot_geoms = set(right_foot_geoms)
    self.floor_geom_id = floor_geom_id

    # 接触缓冲区，用于 mj_contactForce 函数
    self.cf = np.zeros(6, dtype=np.float64)

  def _accumulate_contact_forces(self, target_geom_ids):
    """
    从所有 contact 中筛选：目标脚 geom 与 地面 geom 的接触。
    返回：切向力向量、法向力大小。
    """
    total_force = np.zeros(3)

    for i in range(self.data.ncon):
      con = self.data.contact[i]

      # 判断是否为地面接触
      if not (
        (con.geom1 in target_geom_ids and con.geom2 == self.floor_geom_id)
        or (con.geom2 in target_geom_ids and con.geom1 == self.floor_geom_id)
      ):
        continue

      # 获取接触力（6维：3力 + 3力矩）
      mujoco.mj_contactForce(self.model, self.data, i, self.cf)

      force = self.cf[:3]  # 取力分量

      # 法向力大小（沿接触法线方向）
      # normal_dir = con.frame[0:3]       # 该接触的法线方向向量
      # fn = np.dot(f, normal_dir)        # 法向分量大小

      # # 切向力向量（力 - 法向分量 * 法向方向）
      # ft_vec = f - fn * normal_dir
      total_force += force
    Fn = max(total_force[2], 0.0)  # 法向力（假设z为竖直方向）
    Ft = np.linalg.norm(total_force[:2])  # 切向力大小

    return Ft, Fn

  def get_left_foot_friction(self):
    tan, normal = self._accumulate_contact_forces(self.left_foot_geoms)
    friction_mag = np.linalg.norm(tan)
    mu = friction_mag / normal if normal > 1e-6 else 0.0
    return tan, normal, mu

  def get_right_foot_friction(self):
    tan, normal = self._accumulate_contact_forces(self.right_foot_geoms)
    friction_mag = np.linalg.norm(tan)
    mu = friction_mag / normal if normal > 1e-6 else 0.0
    return tan, normal, mu
