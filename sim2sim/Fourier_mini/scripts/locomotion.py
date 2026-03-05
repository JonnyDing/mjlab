import time

import mujoco
import mujoco.viewer
import numpy as np
import onnxruntime
import torch


def quat_rotate_inverse_np(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate a vector by the inverse of a quaternion along the last dimension of q and v (NumPy version).

    Args:
        q: The quaternion in (w, x, y, z). Shape is (..., 4).
        v: The vector in (x, y, z). Shape is (..., 3).

    Returns:
        The rotated vector in (x, y, z). Shape is (..., 3).
    """
    q_w = q[..., 0]
    q_vec = q[..., 1:]

    # Component a: v * (2.0 * q_w^2 - 1.0)
    a = v * np.expand_dims(2.0 * q_w**2 - 1.0, axis=-1)

    # Component b: cross(q_vec, v) * q_w * 2.0
    b = np.cross(q_vec, v, axis=-1) * np.expand_dims(q_w, axis=-1) * 2.0

    # Component c: q_vec * dot(q_vec, v) * 2.0
    # For efficient computation, handle different dimensionalities
    if q_vec.ndim == 2:
        # For 2D case: use matrix multiplication for better performance
        dot_product = np.sum(q_vec * v, axis=-1, keepdims=True)
        c = q_vec * dot_product * 2.0
    else:
        # For general case: use Einstein summation
        dot_product = np.expand_dims(np.einsum("...i,...i->...", q_vec, v), axis=-1)
        c = q_vec * dot_product * 2.0

    return a - b + c


def matrix_to_quaternion_simple(matrix):
    """
    简化的矩阵转四元数实现
    """
    matrix = np.array(matrix)
    m00, m01, m02 = matrix[0]
    m10, m11, m12 = matrix[1]
    m20, m21, m22 = matrix[2]

    trace = m00 + m11 + m22

    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (m21 - m12) * s
        y = (m02 - m20) * s
        z = (m10 - m01) * s
    elif m00 > m11 and m00 > m22:
        s = 2.0 * np.sqrt(1.0 + m00 - m11 - m22)
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = 2.0 * np.sqrt(1.0 + m11 - m00 - m22)
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = 2.0 * np.sqrt(1.0 + m22 - m00 - m11)
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s

    return np.array([w, x, y, z])


def quaternion_conjugate(q):
    """四元数共轭: [w, x, y, z] -> [w, -x, -y, -z]"""
    return np.array([q[0], -q[1], -q[2], -q[3]])


def yaw_quat(q):
    w, x, y, z = q
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
    return np.array([np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)])


def quaternion_multiply(q1, q2):
    """四元数乘法: q1 ⊗ q2"""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

    return np.array([w, x, y, z])


def get_gravity_orientation(quaternion):
    qw = quaternion[0]
    qx = quaternion[1]
    qy = quaternion[2]
    qz = quaternion[3]

    gravity_orientation = np.zeros(3)

    gravity_orientation[0] = 2 * (-qz * qx + qw * qy)
    gravity_orientation[1] = -2 * (qz * qy + qw * qx)
    gravity_orientation[2] = 1 - 2 * (qw * qw + qz * qz)

    return gravity_orientation


def pd_control(target_q, q, kp, target_dq, dq, kd):
    """Calculates torques from position commands"""
    return (target_q - q) * kp + (target_dq - dq) * kd


xml_path = "/home/djw/Desktop/mjlab/sim2sim/Fourier_mini/fourier_mini_description/mjcf/n1_1.xml"
# xml_path:  "/home/ym/Whole_body_tracking/unitree_description/g1_xml.xml"

simulation_duration = 300.0
simulation_dt = 0.005
control_decimation = 4

if __name__ == "__main__":
    policy_path = (
        "/home/djw/Desktop/mjlab/sim2sim/Fourier_mini/model/locomotion/walk1226.onnx"
    )

    num_actions = 21
    num_obs = 72
    import onnx

    model = onnx.load(policy_path)
    for prop in model.metadata_props:
        if prop.key == "joint_names":
            joint_seq = prop.value.split(",")
        if prop.key == "default_joint_pos":
            joint_pos_array_seq = np.array([float(x) for x in prop.value.split(",")])

        if prop.key == "joint_stiffness":
            stiffness_array_seq = np.array([float(x) for x in prop.value.split(",")])

        if prop.key == "joint_damping":
            damping_array_seq = np.array([float(x) for x in prop.value.split(",")])

        if prop.key == "action_scale":
            action_scale = np.array([float(x) for x in prop.value.split(",")])
        print(f"{prop.key}: {prop.value}")
    
    action = np.zeros(num_actions, dtype=np.float32)
    obs = np.zeros(num_obs, dtype=np.float32)
    gvec = np.array([0, 0, -1], dtype=np.float32)
    commanded_velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # 命令速度：前进速度 0.1 m/s
    counter = 0
    
    # 实时模拟控制（设置为 True 以确保实时模拟，False 以最大速度运行）
    realtime_simulation = True

    # Load robot model
    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    m.opt.timestep = simulation_dt
    policy = onnxruntime.InferenceSession(policy_path)
    action_buffer = np.zeros((num_actions,), dtype=np.float32)
    target_dof_pos = joint_pos_array_seq.copy()
    d.qpos[7:] = target_dof_pos
    
    body_name = "waist_yaw_link"  # robot_ref_body_index=3 motion_ref_body_index=7
    body_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id == -1:
        raise ValueError(f"Body {body_name} not found in model")
    
    with mujoco.viewer.launch_passive(m, d) as viewer:
        start = time.time()
        while viewer.is_running() and time.time() - start < simulation_duration:
            step_start = time.time()
            
            # 执行模拟步
            mujoco.mj_step(m, d)
            
            # 计算PD控制扭矩
            tau = pd_control(
                target_dof_pos,
                d.qpos[7:],
                stiffness_array_seq,
                np.zeros_like(damping_array_seq),
                d.qvel[6:],
                damping_array_seq,
            )
            
            # 应用控制扭矩
            d.ctrl[:] = tau
            
            counter += 1
            
            # 控制更新（每 control_decimation 步执行一次）
            if counter % control_decimation == 0:
                position = d.xpos[body_id]
                quaternion = d.xquat[body_id]
                
                # 构建观测向量 - 按照用户提供的表格结构
                offset = 0
                # 1. command (3,) - 命令速度
                obs[offset:offset + 3] = commanded_velocity
                offset += 3
                
                # 2. base_ang_vel (3,) - 基础角速度
                obs[offset:offset + 3] = d.qvel[3:6]
                offset += 3
                
                # 3. projected_gravity (3,) - 投影重力
                quat_proj = get_gravity_orientation(quaternion)
                obs[offset:offset + 3] = quat_proj
                offset += 3
                
                # 4. joint_pos (21,) - 关节位置（相对于默认位置）
                obs[offset:offset + num_actions] = (d.qpos[7:7 + num_actions] - joint_pos_array_seq)
                offset += num_actions
                
                # 5. joint_vel (21,) - 关节速度
                obs[offset:offset + num_actions] = d.qvel[6:6 + num_actions]
                offset += num_actions
                
                # 6. actions (21,) - 上一动作
                obs[offset:offset + num_actions] = action_buffer
                
                # 运行策略
                obs_tensor = torch.from_numpy(obs).unsqueeze(0)
                action = policy.run(
                    ["actions"],
                    {"obs": obs_tensor.numpy()},
                )[0]
                action = np.asarray(action).reshape(-1)
                action_buffer = action.copy()
                
                # 计算目标关节位置
                target_dof_pos = action * action_scale + joint_pos_array_seq
                target_dof_pos = target_dof_pos.reshape(-1,)
            
            # 同步查看器
            viewer.sync()
            
            # 基础时间保持（确保实时模拟）
            if realtime_simulation:
                time_until_next_step = m.opt.timestep - (time.time() - step_start)
                if time_until_next_step > 0:
                    time.sleep(time_until_next_step)
