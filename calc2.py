import math

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


class SoilLayer:
    """土层类"""
    def __init__(self, name, thickness, unit_weight, cohesion, friction_angle):
        self.name = name 
        self.thickness = thickness 
        self.unit_weight = unit_weight
        self.cohesion = cohesion      
        self.friction_angle = friction_angle
    
    def active_coefficient(self):
        """主动土压力系数 Ka"""
        phi_rad = math.radians(self.friction_angle)
        ka = (math.tan(math.pi/4 - phi_rad/2)) ** 2
        return ka
    
    def passive_coefficient(self):
        """被动土压力系数 Kp"""
        phi_rad = math.radians(self.friction_angle)
        kp = (math.tan(math.pi/4 + phi_rad/2)) ** 2
        return kp

    def __str__(self):
        return (f"【土层信息】名称: {self.name} | 厚度: {self.thickness}m | "
                f"重度: {self.unit_weight}kN/m³ | c: {self.cohesion}kPa | φ: {self.friction_angle}°")

def create_analysis_point(z, position, p_type, layer, current_sigma_v, z_top):
    """
    计算特定深度 z 处的力学参数并返回 AnalysisPoint 对象
    """
    # 计算该深度处的垂直总应力 (当前层顶应力 + 该层内增加部分)
    sigma_v_at_z = current_sigma_v + layer.unit_weight * (z - z_top)
    
    # 计算主动土压力强度 pa
    ka = layer.active_coefficient()
    c_term = 2 * layer.cohesion * math.sqrt(ka)
    pa = sigma_v_at_z * ka - c_term
    
    # 实例化对象
    point = AnalysisPoint(z, position, 0, layer) # layer_index 在外层循环赋予
    point.sigma_v = round(sigma_v_at_z, 2)
    point.pa = round(pa, 2)
    point.point_type = p_type
    
    return point
    
def z_based_data_collection(layers, overload, excavation_depth):
    """
    以高度Z为核心构建整合数据链
    """
    z_axis_data = []
    current_z = 0.0
    current_sigma_v = overload

    for i, layer in enumerate(layers):
        z_top = current_z
        z_bottom = current_z + layer.thickness
        
        # --- 1. 处理层顶 (TOP) ---
        top_p = create_analysis_point(z_top, "TOP", "Interface", layer, current_sigma_v, z_top)
        top_p.layer_index = i
        # 修正：如果层顶正好是开挖面
        if abs(z_top - excavation_depth) < 1e-4:
            top_p.point_type = "Excavation"
        z_axis_data.append(top_p)

        # --- 2. 处理开挖面在层中间的情况 (MID) ---
        if z_top < excavation_depth < z_bottom:
            mid_p = create_analysis_point(excavation_depth, "MID", "Excavation", layer, current_sigma_v, z_top)
            mid_p.layer_index = i
            z_axis_data.append(mid_p)

        # --- 3. 更新参数并处理层底 (BOTTOM) ---
        # 计算该层底部的垂直应力（为下一层做准备）
        next_sigma_v = current_sigma_v + layer.unit_weight * layer.thickness
        
        bot_p = create_analysis_point(z_bottom, "BOTTOM", "Interface", layer, current_sigma_v, z_top)
        bot_p.layer_index = i
        # 修正：如果层底正好是开挖面
        if abs(z_bottom - excavation_depth) < 1e-4:
            bot_p.point_type = "Excavation"
        z_axis_data.append(bot_p)

        # 迭代深度和应力
        current_z = z_bottom
        current_sigma_v = next_sigma_v

    return z_axis_data      

def update_passive_pressures(z_data, excavation_depth):
    for point in z_data:
        # 深度小于开挖面的点，被动压力为 0
        if point.z < excavation_depth - 1e-4:
            point.pp = 0.0
        else:
            # 计算相对于开挖面的相对深度
            dz = max(0, point.z - excavation_depth)
            kp = point.layer.passive_coefficient()
            
            # Pp = γ * dz * Kp + 2c√Kp
            sigma_v_p = point.layer.unit_weight * dz
            c_term = 2 * point.layer.cohesion * math.sqrt(kp)
            
            point.pp = round(sigma_v_p * kp + c_term, 2)
        
        # 顺便更新净压力
        point.p_net = round(point.pa - point.pp, 2)

def find_and_insert_critical_depths(z_axis_data, pile_top_z):
    """
    基于原有解析逻辑寻找临界深度，并更新 z_axis_data。
    计算公式维持不变：delta_z = (c_term/ka - sigma_v) / unit_weight
    """
    critical_points = []
    
    # 遍历现有的数据点，寻找 Pa 跨越零点的区间
    # 我们只需要检查每个土层的 TOP 到 BOTTOM 过程
    i = 0
    while i < len(z_axis_data) - 1:
        p_top = z_axis_data[i]
        p_bot = z_axis_data[i+1]
        
        # 判定条件：同一层内，且压力从负变正
        if p_top.z != p_bot.z and p_top.pa < 0 and p_bot.pa > 0:
            layer = p_top.layer
            ka = layer.active_coefficient()
            c_term = 2 * layer.cohesion * math.sqrt(ka)
            
            # --- 维持你原来的计算逻辑 ---
            # delta_z 是相对于当前层顶的高度
            delta_z = ((c_term / ka) - p_top.sigma_v) / layer.unit_weight
            absolute_z = round(p_top.z + delta_z, 1)
            
            # 桩顶标高过滤
            if absolute_z > pile_top_z:
                # 创建新的分析点对象
                crit_point = AnalysisPoint(absolute_z, "MID", p_top.layer_index, layer)
                crit_point.pa = 0.0  # 定义点，Pa 理论上为 0
                crit_point.sigma_v = round(p_top.sigma_v + layer.unit_weight * delta_z, 2)
                crit_point.point_type = "Critical"
                
                critical_points.append(crit_point)
                
                # 插入到数据链中，确保 z_axis_data 的连续性
                z_axis_data.insert(i + 1, crit_point)
                i += 1  # 跳过新插入的点
                
        i += 1
    
    return critical_points

def fill_inflection_point_data(inflection_point, excavation_depth, z_axis_data):
    """
    为强制生成的反弯点补全 pa, pp, sigma_v 等数据
    """
    layer = inflection_point.layer
    dz = inflection_point.z - excavation_depth  # 相对于开挖面的深度
    
    # 1. 计算垂直应力 sigma_v
    # 需要先获取开挖面处的垂直应力基数
    try:
        sigma_v_exc = next(p.sigma_v for p in z_axis_data if p.point_type == "Excavation")
    except StopIteration:
        # 如果没找到标记，则根据深度简单累加（这种逻辑更稳健）
        sigma_v_exc = sum(l.unit_weight * l.thickness for l in layers[:inflection_point.layer_index])
        
    # 该点的总垂直应力 = 开挖面处应力 + 该层内增加的应力
    inflection_point.sigma_v = round(sigma_v_exc + layer.unit_weight * dz, 2)

    # 2. 计算主动土压力 pa
    ka = layer.active_coefficient()
    c_a = 2 * layer.cohesion * math.sqrt(ka)
    inflection_point.pa = round(inflection_point.sigma_v * ka - c_a, 2)

    # 3. 计算被动土压力 pp
    # 被动区通常不考虑开挖面以上的超载，垂直应力只算 dz 这一段
    kp = layer.passive_coefficient()
    c_p = 2 * layer.cohesion * math.sqrt(kp)
    sigma_v_passive = layer.unit_weight * dz
    inflection_point.pp = round(sigma_v_passive * kp + c_p, 2)

    # 4. 设置净压力
    # 既然是人工指定的“反弯点”，在后续力矩平衡计算中，通常将其 p_net 设为 0
    # 但为了数据真实性，我们可以记录真实值，或者强制设为 0
    inflection_point.p_net = 0.0 
    
    return inflection_point

def find_layer_at_depth(z_axis_data, target_depth, tolerance=1e-6):
    """
    在 z_data 中根据深度定位 nominal_z 所在的土层。
    共享界面深度归属到下伏土层，但插入位置应落在上一层 BOTTOM 与下一层 TOP 之间。
    """
    layer_bounds = {}

    for idx, point in enumerate(z_axis_data):
        bounds = layer_bounds.setdefault(
            point.layer_index,
            {"top": None, "top_index": None, "bottom": None, "bottom_index": None, "indices": []}
        )
        bounds["indices"].append(idx)

        if point.position == "TOP" and bounds["top"] is None:
            bounds["top"] = point
            bounds["top_index"] = idx
        elif point.position == "BOTTOM":
            bounds["bottom"] = point
            bounds["bottom_index"] = idx

    ordered_layers = sorted(
        (bounds for bounds in layer_bounds.values() if bounds["top"] and bounds["bottom"]),
        key=lambda item: item["top"].z
    )

    for pos, bounds in enumerate(ordered_layers):
        top_z = bounds["top"].z
        bottom_z = bounds["bottom"].z
        is_last_layer = pos == len(ordered_layers) - 1

        if abs(target_depth - top_z) <= tolerance:
            result = dict(bounds)

            if pos > 0 and abs(ordered_layers[pos - 1]["bottom"].z - top_z) <= tolerance:
                result["insert_index"] = result["top_index"]
            else:
                result["insert_index"] = result["top_index"] + 1

            return result

        if top_z - tolerance <= target_depth < bottom_z:
            return bounds

        if is_last_layer and abs(target_depth - bottom_z) <= tolerance:
            result = dict(bounds)
            result["insert_index"] = result["bottom_index"]
            return result

    return None

def find_insert_index_in_layer(z_axis_data, layer_info, target_depth, tolerance=1e-6):
    """
    计算反弯点在目标土层中的插入位置，确保落在该层 TOP 与 BOTTOM 之间。
    """
    if "insert_index" in layer_info:
        return layer_info["insert_index"]

    insert_index = layer_info["indices"][-1]

    for idx in layer_info["indices"]:
        point = z_axis_data[idx]

        if point.z < target_depth - tolerance:
            insert_index = idx + 1
            continue

        if abs(point.z - target_depth) <= tolerance:
            if point.position == "TOP":
                has_same_depth_before = any(
                    abs(z_data_point.z - target_depth) <= tolerance
                    for z_data_point in z_axis_data[:idx]
                )
                return idx if has_same_depth_before else idx + 1
            if point.position == "BOTTOM":
                return idx
            return idx + 1

        return idx

    return insert_index

def find_and_insert_inflection_point(z_axis_data, excavation_depth):
    """
    寻找反弯点：优先寻找 Pa - Pp = 0 的解析点；
    若无法确定（被动始终大于主动），则取 1.2 倍开挖深度处作为名义零点。
    """
    found_parse_point = False
    
    # 1. 尝试寻找解析零点 (Pa - Pp = 0)
    for i in range(len(z_axis_data) - 1):
        p_top = z_axis_data[i]
        p_bot = z_axis_data[i+1]
        
        if p_top.z < excavation_depth - 1e-4:
            continue
            
        # 判定是否存在符号翻转
        if p_top.p_net > 0 and p_bot.p_net < 0:
            found_parse_point = True
            return True 

    # 2. 如果没有找到零点（坑底土层太强），执行退路逻辑
    if not found_parse_point:
        nominal_z = round(1.2 * excavation_depth, 3)

        layer_info = find_layer_at_depth(z_axis_data, nominal_z)
        if layer_info:
            layer = layer_info["top"].layer

            # 创建名义反弯点
            inflection_point = AnalysisPoint(nominal_z, "MID", layer_info["top"].layer_index, layer)
            inflection_point.point_type = "Inflection"
            inflection_point.layer_name = f"{layer.name}"

            # 在该深度处补算一次 pa 和 pp 保证数据完整
            fill_inflection_point_data(inflection_point, excavation_depth, z_axis_data)
            insert_index = find_insert_index_in_layer(z_axis_data, layer_info, nominal_z)
            z_axis_data.insert(insert_index, inflection_point)
            print(f"提示：未发现自然土压力零点，已取 1.2H ({nominal_z}m) 作为名义零点。")
            return True
                 
    return False

def calculate_force_and_centroid(p1, p2, force_type="pa"):
    """
    底层数学计算：计算两点间的合力(f)和形心深度(z_c)
    :param force_type: "pa" (主动) 或 "pp" (被动)
    """
    h = p2.z - p1.z
    if h <= 1e-6:
        return 0.0, 0.0

    # 提取压力值
    v1 = getattr(p1, force_type)
    v2 = getattr(p2, force_type)

    # 关键修正：如果是主动压力，负值替换为 0
    if force_type == "pa":
        v1 = max(0.0, v1)
        v2 = max(0.0, v2)
    
    # 梯形面积公式 (合力)
    f = (v1 + v2) * h / 2
    
    # 梯形形心公式 (相对于 p1.z 的偏移)
    if abs(v1 + v2) > 1e-6:
        z_c_rel = (h / 3) * ((2 * v1 + v2) / (v1 + v2))
    else:
        z_c_rel = h / 2
        
    return f, z_c_rel

def identify_business_intervals(z_data, target_types=None):
    """
    通用区间识别函数：
    :param z_data: 包含 Point 对象的列表
    :param target_types: 想要提取的类型列表，如 ["Critical", "Inflection", "Excavation"]
    :return: 仅包含 [起点, 终点] 的区间列表，跳过所有中间点
    """
    if target_types is None:
        # 默认处理这三种业务类型
        target_types = ["Critical", "Inflection", "Excavation"]
    
    # 配置映射：定义不同类型的搜索方向和目标边界
    # direction: 1 为向下(深)搜, -1 为向上(浅)搜
    # boundary: 目标边界标签
    config = {
        "Critical": {"direction": 1, "boundary": "BOTTOM"},
        "Inflection": {"direction": -1, "boundary": "TOP"},
        "Excavation": {"direction": 1, "boundary": "BOTTOM"}  # 新增：向下找层底
    }
    
    # 深度比较容差：用于处理浮点误差与同深度接口点（上一层底=下一层顶）
    z_tolerance = 1e-6
    point_index_map = {point: idx for idx, point in enumerate(z_data)}
    
    intervals = []
    down_intervals = []
    up_intervals = []
    
    for i, p in enumerate(z_data):
        # 只有当点的类型在目标列表且有对应配置时才处理
        if p.point_type in target_types and p.point_type in config:
            cfg = config[p.point_type]
            direction = cfg["direction"]
            boundary = cfg["boundary"]
            
            # 确定搜索索引范围
            if direction == 1:
                search_range = range(i + 1, len(z_data))
            else:
                search_range = range(i, -1, -1)
            
            # 执行查找
            for j in search_range:
                # 严格匹配边界标签，并且通常建议匹配同一土层 (layer_index)
                if z_data[j].position == boundary and z_data[j].layer_name == p.layer_name:
                    # 统一返回 [浅点, 深点] 的顺序
                    if direction == 1:
                        segment = [p, z_data[j]]
                        down_intervals.append(segment)
                    else:
                        segment = [z_data[j], p]
                        up_intervals.append(segment)
                    intervals.append(segment)
                    break # 找到最近的一个边界后立即跳出当前点的搜寻
    
    # 补齐“向下区间”与“反弯点向上区间”之间跨层缺失区间
    # 典型场景：开挖较深时，反弯点在更深土层，导致中间层段遗漏
    if "Inflection" in target_types and down_intervals and up_intervals:
        deepest_down_point = max((seg[1] for seg in down_intervals), key=lambda p: p.z)
        shallowest_up_point = min((seg[0] for seg in up_intervals), key=lambda p: p.z)
        
        if deepest_down_point.z < shallowest_up_point.z - z_tolerance:
            start_idx = point_index_map[deepest_down_point]
            end_idx = point_index_map[shallowest_up_point]
            
            prev = deepest_down_point
            for k in range(start_idx + 1, end_idx + 1):
                curr = z_data[k]
                
                # 同深度接口点（上一层底=下一层顶）只更新锚点，不形成区间
                if abs(curr.z - prev.z) < z_tolerance:
                    prev = curr
                    continue
                
                intervals.append([prev, curr])
                prev = curr
    
    # 统一按深度从浅到深排序，便于后续计算与调试
    intervals.sort(key=lambda seg: (seg[0].z, seg[1].z))
    
    return intervals

def compute_soil_pressure(z_data):
    report = {"active": [], "passive": []}

    # --- 主动土压力计算 ---
    # 范围：Critical (向下) 和 Inflection (向上)
    active_segments = identify_business_intervals(z_data, ["Critical", "Inflection"])
    for seg in active_segments:
        f, z_c_rel = calculate_force_and_centroid(seg[0], seg[1], "pa")
        z_c = seg[1].z - z_c_rel
        if f > 0:
            report["active"].append({"range": f"{seg[0].z}-{seg[1].z}", "f": f, "z_c": z_c})

    # --- 被动土压力计算 ---
    # 范围：Excavation (向下) 和 Inflection (向上)
    # 注意：根据你的要求，被动压力计算范围由这两个标记确定
    passive_segments = identify_business_intervals(z_data, ["Excavation", "Inflection"])
    for seg in passive_segments:
        f, z_c_rel = calculate_force_and_centroid(seg[0], seg[1], "pp")
        z_c = seg[1].z - z_c_rel
        if f > 0:
            report["passive"].append({"range": f"{seg[0].z}-{seg[1].z}", "f": f, "z_c": z_c})

    return report

def calculate_strut_force(pressure_report, z_inflection, z_strut):
    """
    根据力矩平衡计算支撑轴力
    :param pressure_report: 包含 active 和 passive 列表的字典
    :param z_inflection: 反弯点深度 (m)
    :param z_strut: 支撑中心深度 (m)
    """
    sum_moment = 0.0
    
    # 1. 计算主动土压力对反弯点的力矩 (通常产生向坑内的转动矩)
    # 这里的力矩方向定义：F_active > 0, 力臂 (z_inflection - z_c)
    for item in pressure_report["active"]:
        force = item["f"]
        arm = z_inflection - item["z_c"]
        sum_moment += force * arm
        
    # 2. 计算被动土压力对反弯点的力矩 (通常产生向坑外的转动矩)
    # 被动压力方向与主动相反，故取负值
    for item in pressure_report["passive"]:
        force = item["f"]
        arm = z_inflection - item["z_c"]
        sum_moment -= force * arm  # 减去被动矩
        
    # 3. 计算支撑力臂
    strut_arm = z_inflection - z_strut
    
    if abs(strut_arm) < 1e-6:
        return 0.0 # 支撑位置就在反弯点上，无法计算轴力
    
    # 4. 根据 M_strut + M_soil = 0 => R * arm = -sum_moment
    # R = -sum_moment / strut_arm
    # 得到的 R 为正值表示支撑受压
    strut_force = -sum_moment / strut_arm
    
    return abs(round(strut_force, 2))

def calculate_multi_strut_force(pressure_report, z_inflection, current_strut_pos, previous_struts=None):
    """
    计算当前道支撑力，考虑已安装支撑的影响
    :param previous_struts: 已安装支撑列表，例如 [{"pos": 2.0, "force": 150.5}, ...]
    """
    sum_moment = 0.0
    
    # 1. 计算所有土压力对【当前反弯点】的力矩
    for item in pressure_report["active"]:
        sum_moment += item["f"] * (z_inflection - item["z_c"])
    for item in pressure_report["passive"]:
        sum_moment -= item["f"] * (z_inflection - item["z_c"])
        
    # 2. 计算【旧支撑】对当前反弯点的力矩
    if previous_struts:
        for strut in previous_struts:
            # 旧支撑力 R1 产生的矩：R1 * (z_inf2 - z_strut1)
            # 方向注意：支撑力方向通常与主动土压力相反
            strut_arm = z_inflection - strut["pos"]
            sum_moment -= strut["force"] * strut_arm 

    # 3. 计算【当前支撑】的力臂
    current_arm = z_inflection - current_strut_pos
    
    # 4. 平衡方程：R_current * current_arm + sum_moment = 0
    # R_current = -sum_moment / current_arm
    if abs(current_arm) < 1e-6: return 0.0
    
    current_force = -sum_moment / current_arm
    return abs(round(current_force, 2))

# if __name__ == "__main__":
#     depth_excavation = 8.5
#     depth_pile = 1.5
#     overload = 30
#     depth_struc = 2             # 支撑点位置

#     layers = [
#         SoilLayer("杂填土", 0.6, 18.2, 6.0, 12.3),
#         SoilLayer("素填士", 0.7, 18.7, 18.0, 12.3),
#         SoilLayer("粉质黏土", 3.3, 19.0, 26.0, 14.3),
#         SoilLayer("粉质黏土", 4.4, 19.8, 43.2, 21.0),
#         SoilLayer("粉质黏土混卵砾石", 5.1, 20.5, 28.5, 23.5),
#         SoilLayer("强风化粉砂岩", 7.4, 21.0, 28.5, 22.5),
#         SoilLayer("中风化粉砂岩粉砂岩", 25.6, 22.2, 55.1, 30.7)
#     ]
    
#     z_data = z_based_data_collection(layers, overload, depth_excavation)

#     critical_list = find_and_insert_critical_depths(z_data, depth_pile)
    
#     update_passive_pressures(z_data, depth_excavation)

#     find_and_insert_inflection_point(z_data, depth_excavation)
#     # for point in z_data:
#     #     #if point.point_type == "Critical" or point.point_type == "Interface" or point.point_type == "Inflection":
#     #     print(f"高度: {point.z:>6}m | "
#     #           f"位置: {point.position:<6} | "
#     #           f"土层: {point.layer_name:<10} | "
#     #           f"主动压力: {point.pa:>8} kPa | "
#     #           f"被动压力: {point.pp:>8} kPa | "
#     #           f"静土压力: {point.p_net:>8} kPa | "
#     #           f"类型: {point.point_type:>8}"
#     #           )

#     result_pressure = compute_soil_pressure(z_data)
#     print(result_pressure)

#     depth_inflection = next(p.z for p in z_data if p.point_type == "Inflection")
#     force = calculate_strut_force(result_pressure, depth_inflection, depth_struc)
#     print(force)


if __name__ == "__main__":
    layers = [
        SoilLayer("杂填土", 0.6, 18.2, 6.0, 12.3),
        SoilLayer("素填士", 0.7, 18.7, 18.0, 12.3),
        SoilLayer("粉质黏土", 3.3, 19.0, 26.0, 14.3),
        SoilLayer("粉质黏土", 4.4, 19.8, 43.2, 21.0),
        SoilLayer("粉质黏土混卵砾石", 5.1, 20.5, 28.5, 23.5),
        SoilLayer("强风化粉砂岩", 7.4, 21.0, 28.5, 22.5),
        SoilLayer("中风化粉砂岩粉砂岩", 25.6, 22.2, 55.1, 30.7)
    ]
    # 定义施工工况：(当前开挖深度, 当前新增的支撑位置)
    # 第一步：开挖至 3.0m，加第一道支撑 at 2.0m
    # 第二步：开挖至 8.5m，加第二道支撑 at 7.0m
    construction_stages = [
        {"excavation": 8.5, "strut": 2.0},
        {"excavation": 13, "strut": 8.0}
    ]
    
    overload = 30
    depth_pile = 1.5 # 桩入土深度或特定参数
    
    installed_struts = []
    # final_forces = []

    index = 1
    for stage in construction_stages:
        curr_excavation = stage["excavation"]
        curr_strut = stage["strut"]
        
        # 1. 重新生成当前开挖深度下的数据链
        # 随着 excavation 改变，土压力分布和被动区起点都会改变
        z_data = z_based_data_collection(layers, overload, curr_excavation)
        
        # 2. 插入关键点并更新压力
        find_and_insert_critical_depths(z_data, depth_pile)
        update_passive_pressures(z_data, curr_excavation)
        find_and_insert_inflection_point(z_data, curr_excavation)

        # for point in z_data:
        #     print(f"高度: {point.z:>6}m | "
        #           f"位置: {point.position:<6} | "
        #           f"土层: {point.layer_name:<10} | "
        #           f"主动压力: {point.pa:>8} kPa | "
        #           f"被动压力: {point.pp:>8} kPa | "
        #           f"静土压力: {point.p_net:>8} kPa | "
        #           f"类型: {point.point_type:>8}"
        #           )
        # 3. 计算当前工况的压力区间
        result_pressure = compute_soil_pressure(z_data)
        # print(result_pressure)
        # 4. 获取当前工况的反弯点
        try:
            depth_inflection = next(p.z for p in z_data if p.point_type == "Inflection")
            
            # 5. 计算支撑力
            # 注意：在多支护计算中，通常是用“等值梁法”或其他简化法
            # 这里沿用你对反弯点取矩的逻辑
            # force = calculate_strut_force(result_pressure, depth_inflection, curr_strut)
            force = calculate_multi_strut_force(result_pressure, depth_inflection, curr_strut, installed_struts)

            installed_struts.append({"pos": curr_strut, "force": force})
            print(f"开挖至 {curr_excavation}m，支撑({curr_strut}m) 第{index}支撑轴力为: {force}")

        except StopIteration:
            print(f"警告：开挖深度 {curr_excavation}m 处未发现反弯点，可能由于入土深度不足。")
        index += 1
    # 输出所有阶段结果
    # for res in final_forces:
    #     print(f"开挖至{res['stage_excavation']}m时，第{final_forces.index(res)+1}道支撑({res['strut_pos']}m)轴力: {res['force']} kN/m")
