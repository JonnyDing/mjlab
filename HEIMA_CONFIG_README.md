# Heima机器人执行器配置说明

## 配置概述

已为Heima机器人创建完整的执行器配置 ([heima_constants.py](src/mjlab/asset_zoo/robots/heima/heima_constants.py))。

## 电机规格

### 1. X6执行器（踝关节 - 并联配置）
- **应用关节**: `ankle_pitch`, `ankle_roll`
- **减速比**: 19.61
- **配置**: 2个X6电机并联（参考G1脚踝设计）
- **单电机参数**:
  - armature: 0.005 kg⋅m²
  - stiffness: 19.74 Nm/rad
  - damping: 1.26 Nm⋅s/rad
- **并联后参数** (×2):
  - armature: 0.010 kg⋅m²
  - stiffness: 39.48 Nm/rad
  - damping: 2.51 Nm⋅s/rad
  - effort_limit: 120 Nm

### 2. X12执行器（髋/膝关节）
- **应用关节**: `hip_roll`, `hip_yaw`, `knee_pitch`
- **减速比**: 20
- **参数**:
  - armature: 0.020 kg⋅m²
  - stiffness: 78.96 Nm/rad
  - damping: 5.03 Nm⋅s/rad
  - effort_limit: 320 Nm

### 3. X15执行器（髋pitch关节）
- **应用关节**: `hip_pitch`
- **减速比**: 20.25
- **参数**:
  - armature: 0.040 kg⋅m²
  - stiffness: 157.91 Nm/rad
  - damping: 10.05 Nm⋅s/rad
  - effort_limit: 450 Nm

## 计算方法

### Armature（等效惯量）

由于缺少各级转子惯量数据，采用基于减速比和典型电机特性的估算值：
- **X6**: 0.005 kg⋅m²（小型电机）
- **X12**: 0.020 kg⋅m²（中型电机）
- **X15**: 0.040 kg⋅m²（大型电机）

这些值可根据实际硬件测试进行调整。

### Stiffness（刚度）

使用二阶系统模型，基于自然频率计算：

```
stiffness = armature × ω_n²
```

其中：
- 自然频率 ω_n = 2π × 10 = 62.83 rad/s (10 Hz)

**示例计算（X12）**:
```
stiffness = 0.020 × (62.83)² = 78.96 Nm/rad
```

### Damping（阻尼）

使用临界阻尼比计算：

```
damping = 2 × ζ × armature × ω_n
```

其中：
- 阻尼比 ζ = 2.0（过阻尼，参考G1配置）

**示例计算（X12）**:
```
damping = 2 × 2.0 × 0.020 × 62.83 = 5.03 Nm⋅s/rad
```

## 并联配置处理

脚踝关节使用2个X6电机并联驱动（类似G1的腰部和脚踝设计）：

- **等效armature** = 单电机armature × 2
- **等效stiffness** = 单电机stiffness × 2
- **等效damping** = 单电机damping × 2
- **等效effort_limit** = 单电机effort_limit × 2

这种处理假设并联机构在标称配置下的1:1传动比。

## 参数比值分析

| 比较 | 比值 | 说明 |
|------|------|------|
| X6并联/X12 | 0.5 | 脚踝惯量约为髋/膝的一半 |
| X15/X12 | 2.0 | 髋pitch惯量是其他髋关节的2倍 |
| X15/X6并联 | 4.0 | 髋pitch惯量是脚踝的4倍 |

## 动作缩放因子

每个关节的动作缩放因子计算为：

```
action_scale = 0.25 × effort_limit / stiffness
```

典型值：
- 脚踝：~0.76
- 髋pitch：~0.71
- 髋roll/yaw、膝：~1.01

## 参考文件

配置设计参考了以下文件：
1. [g1_constants.py](src/mjlab/asset_zoo/robots/unitree_g1/g1_constants.py) - 并联配置、计算方法
2. [h1_2_constants.py](src/mjlab/asset_zoo/robots/unitree_h1_2/h1_2_constants.py) - 直接参数配置方法
3. [actuator.py](src/mjlab/utils/actuator.py) - 惯量反射计算函数

## 使用示例

```python
from mjlab.asset_zoo.robots.heima.heima_constants import get_heima_robot_cfg
from mjlab.entity.entity import Entity

# 创建机器人实体
robot_cfg = get_heima_robot_cfg()
robot = Entity(robot_cfg)

# 编译并使用
model = robot.spec.compile()
```

## 测试验证

运行测试脚本：
```bash
source heima_loco/bin/activate
python test_heima_config.py
```

或启动MuJoCo查看器：
```bash
source heima_loco/bin/activate
python src/mjlab/asset_zoo/robots/heima/heima_constants.py
```

## 参数调优建议

如果有实际硬件数据，建议调整以下参数：

1. **Armature值**: 根据电机转子惯量和实际传动链测量
2. **自然频率**: 根据实际控制带宽调整（当前10Hz可能偏保守）
3. **阻尼比**: 根据实际系统响应调整（2.0为过阻尼，可能需要降低）
4. **Effort limits**: 根据实际电机输出力矩和安全限制调整

## 已知限制

1. **转子惯量估算**: 由于没有各级转子惯量数据，armature值为估算值
2. **传动链简化**: 假设简单的减速比传动，未考虑复杂的四杆机构（除脚踝）
3. **脚踝并联简化**: 假设标称1:1传动比，实际传动比可能随构型变化

建议在实际应用中通过系统辨识或硬件测试来精确确定这些参数。
