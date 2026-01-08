import time
import pygame
from multiprocessing import Process, Queue

import mujoco
import mujoco.viewer
import numpy as np
import onnxruntime
import torch


class JoystickProcess(Process):
    def __init__(self, buffer):
        super().__init__()
        
        self.buffer = buffer
        
    def run(self) -> None:
        pygame.init()
        pygame.joystick.init()
        
        # 等待手柄连接
        while pygame.joystick.get_count() == 0:
            print("等待手柄连接...")
            time.sleep(1)
            pygame.joystick.quit()
            pygame.joystick.init()
        
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        
        self.num_buttons = joystick.get_numbuttons()
        self.num_axes = joystick.get_numaxes()
        self.num_hats = joystick.get_numhats()
        
        print(f"手柄已连接: {joystick.get_name()}")
        print(f"按钮数量: {self.num_buttons}")
        print(f"轴数量: {self.num_axes}")
        print(f"帽子开关数量: {self.num_hats}")
        
        while True:
            pygame.event.pump()  # 处理事件队列
            
            data = {
                "joystick": self.get_joystick(joystick),
                "buttons": self.get_btns(joystick)
            }
            self.buffer.put(data)
            time.sleep(0.01)  # 10ms 更新频率
    
    def _get_axis(self, joystick, axis):
        return joystick.get_axis(axis)

    def _get_button(self, joystick, button):
        return joystick.get_button(button)

    def _get_hat(self, joystick, hat):
        return joystick.get_hat(hat)
    
    def get_joystick(self, joystick):
        l_x = self._get_axis(joystick, 0)  # left stick x: right positive
        l_y = self._get_axis(joystick, 1)  # left stick y: down positive
        r_x = self._get_axis(joystick, 2)  # right stick x: right positive
        r_y = self._get_axis(joystick, 3)  # right stick y: down positive
        
        # 根据用户反馈修正映射：
        # 前后（推/拉摇杆）控制x方向（前进/后退）
        # 左右（左右摇动摇杆）控制y方向（左右移动）
        # 所以：x = -l_y（前后），y = l_x（左右）
        left_stick = [-l_y, l_x]  # x方向：前后，y方向：左右
        right_stick = [r_x, -r_y]  # 右摇杆保持原样：x控制yaw
        
        return (left_stick, right_stick)
    
    def get_btns(self, joystick):
        A_button = self._get_button(joystick, 0)
        B_button = self._get_button(joystick, 1)
        X_button = self._get_button(joystick, 2)
        Y_button = self._get_button(joystick, 3)
        
        return [A_button, B_button, X_button, Y_button]


class Joystick:
    def __init__(self):
        self.last_data = {
            "joystick": ([0, 0], [0, 0]),
            "buttons": [0, 0, 0, 0]
        }
        self.joystick_buffer = Queue(maxsize=100)
        
        self.joystick_process = JoystickProcess(buffer=self.joystick_buffer)
        self.joystick_process.daemon = True
        self.joystick_process.start()
        
    def read(self):
        try:
            data = self.joystick_buffer.get_nowait()
            self.last_data = data.copy()
        except:
            data = self.last_data
        
        return data
    
    def get_velocity_command(self):
        """从手柄读取速度命令并应用限制和灵敏度控制"""
        data = self.read()
        left_stick, right_stick = data["joystick"]
        
        # 灵敏度参数
        sensitivity = 0.5  # 灵敏度系数 (0.0-1.0)
        deadzone = 0.1     # 死区大小，小于此值的输入视为0
        
        # 处理左摇杆输入（x,y方向）
        x_input = left_stick[0]
        y_input = left_stick[1]
        
        # 应用死区
        if abs(x_input) < deadzone:
            x_input = 0.0
        if abs(y_input) < deadzone:
            y_input = 0.0
        
        # 应用灵敏度（平方曲线，提供更精细的控制）
        x_input = np.sign(x_input) * (abs(x_input) ** (1.0 / (sensitivity + 0.5)))
        y_input = np.sign(y_input) * (abs(y_input) ** (1.0 / (sensitivity + 0.5)))
        
        # 处理右摇杆输入（yaw方向）
        yaw_input = right_stick[0]
        
        # 应用死区
        if abs(yaw_input) < deadzone:
            yaw_input = 0.0
        
        # 应用灵敏度
        yaw_input = np.sign(yaw_input) * (abs(yaw_input) ** (1.0 / (sensitivity + 0.5)))
        
        # 应用限制
        x_vel = max(-1.0, min(1.0, x_input))  # x方向限制: (-1, 1)
        y_vel = max(-1.0, min(1.0, y_input))  # y方向限制: (-1, 1)
        yaw_vel = max(-0.5, min(0.5, yaw_input))  # yaw方向限制: (-0.5, 0.5)
        
        return np.array([x_vel, y_vel, yaw_vel], dtype=np.float32)


def quat_rotate_inverse_np(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate a vector by the inverse of a quaternion along the last dimension of q and v (NumPy version)."""
    q_w = q[..., 0]
    q_vec = q[..., 1:]

    a = v * np.expand_dims(2.0 * q_w**2 - 1.0, axis=-1)
    b = np.cross(q_vec, v, axis=-1) * np.expand_dims(q_w, axis=-1) * 2.0
    
    if q_vec.ndim == 2:
        dot_product = np.sum(q_vec * v, axis=-1, keepdims=True)
        c = q_vec * dot_product * 2.0
    else:
        dot_product = np.expand_dims(np.einsum("...i,...i->...", q_vec, v), axis=-1)
        c = q_vec * dot_product * 2.0

    return a - b + c


def matrix_to_quaternion_simple(matrix):
    """简化的矩阵转四元数实现"""
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
simulation_duration = 300.0
simulation_dt = 0.005
control_decimation = 4

if __name__ == "__main__":
    policy_path = "/home/djw/Desktop/mjlab/sim2sim/Fourier_mini/model/locomotion/walk1226.onnx"

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
    counter = 0
    
    # 初始化手柄
    print("初始化手柄...")
    joystick = Joystick()
    time.sleep(1)  # 给手柄初始化一些时间
    
    # 实时模拟控制
    realtime_simulation = True

    # 加载机器人模型
    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    m.opt.timestep = simulation_dt
    policy = onnxruntime.InferenceSession(policy_path)
    action_buffer = np.zeros((num_actions,), dtype=np.float32)
    target_dof_pos = joint_pos_array_seq.copy()
    d.qpos[7:] = target_dof_pos
    
    body_name = "waist_yaw_link"
    body_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id == -1:
        raise ValueError(f"Body {body_name} not found in model")
    
    print("开始模拟...")
    print("使用手柄控制:")
    print("  左摇杆: 控制x,y方向速度 (x:左右, y:前后)")
    print("  右摇杆: 控制yaw方向速度 (x:左右旋转)")
    print("  速度限制: x,y方向(-1,1), yaw方向(-0.5,0.5)")
    print("  按Ctrl+C退出")
    
    with mujoco.viewer.launch_passive(m, d) as viewer:
        start = time.time()
        while viewer.is_running() and time.time() - start < simulation_duration:
            step_start = time.time()
            
            # 从手柄读取速度命令
            commanded_velocity = joystick.get_velocity_command()
            
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
                
                # 构建观测向量
                offset = 0
                # 1. command (3,) - 命令速度（来自手柄）
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
                
                # 显示当前速度命令
                if counter % (control_decimation * 10) == 0:  # 每10个控制周期显示一次
                    print(f"速度命令: x={commanded_velocity[0]:.2f}, y={commanded_velocity[1]:.2f}, yaw={commanded_velocity[2]:.2f}")
            
            # 同步查看器
            viewer.sync()
            
            # 基础时间保持
            if realtime_simulation:
                time_until_next_step = m.opt.timestep - (time.time() - step_start)
                if time_until_next_step > 0:
                    time.sleep(time_until_next_step)
    
    print("模拟结束")