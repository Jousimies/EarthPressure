土压力计算

# 一、 环境配置说明
## Python

``` shell
	brew install python
```

验证版本: python3 --version（应为 3.10 或更高）

## 项目结构
创建一个文件夹，将 SoilLayer 类、Point 类定义以及识别和计算函数放入同一文件（如 main.py）或模块中。


# 二、完整代码实现
代码集成了多点路径识别、跨土层压力计算以及多道支撑力平衡计算逻辑。

``` python
class AnalysisPoint:
    """
    分析点类：整合高度Z、土层属性对象与计算结果。
    """
    def __init__(self, depth: float, position: str, layer_index: int, layer_obj):
        # --- 基础定位信息 ---
        self.z = round(depth, 3)           # 绝对深度 (m)
        self.position = position           # "TOP" 或 "BOTTOM"
        self.layer_index = layer_index     # 土层索引
        self.layer = layer_obj             # 直接持有土层对象引用 (SoilLayer instance)
        self.layer_name = layer_obj.name   # 冗余存储名称方便显示

        # --- 物理力学状态 ---
        self.sigma_v = 0.0                 # 垂直应力 (kPa)
        self.pa = 0.0                      # 主动土压力强度 (kPa)
        self.pp = 0.0                      # 被动土压力强度 (kPa)
        self.p_net = 0.0                   # 净土压力 (pa - pp) (kPa)

        # --- 累积计算结果 ---
        self.cum_force = 0.0               # 累积合力 (kN/m)
        self.cum_moment = 0.0              # 累积力矩 (kN·m/m)
        
        # --- 标记属性 ---
        self.point_type = "Normal"         
        self.is_active_zone = True         

    def __repr__(self):
        return (f"<Point Z:{self.z}m | {self.position} | {self.layer_name} | "
                f"Pa:{self.pa:.2f} | Pp:{self.pp:.2f}>")

    def to_dict(self):
        return {
            "深度(m)": self.z,
            "位置": self.position,
            "土层": self.layer_name,
            "垂直应力": self.sigma_v,
            "主动土压力": self.pa,
            "被动土压力": self.pp,
            "净压力": self.p_net,
            "累积合力": self.cum_force,
            "点类型": self.point_type
        }

```

# 三、运行与调试
在终端输入 python3 calc.py

# 四、通信图
- calc2.py 通信图：`/home/runner/work/EarthPressure/EarthPressure/calc2_通信图.md`
