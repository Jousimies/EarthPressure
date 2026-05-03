import csv
import math
from typing import List, Dict, Optional

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

    def active_cohesion_term(self):
        ka = self.active_coefficient()
        return 2 * self.cohesion * math.sqrt(ka)
    
    def passive_coefficient(self):
        """被动土压力系数 Kp"""
        phi_rad = math.radians(self.friction_angle)
        kp = (math.tan(math.pi/4 + phi_rad/2)) ** 2
        return kp

    def passive_cohesion_term(self):
        kp = self.passive_coefficient()
        return 2 * self.cohesion * math.sqrt(kp)

    def __str__(self):
        return (f"【土层信息】名称: {self.name} | 厚度: {self.thickness}m | "
                f"重度: {self.unit_weight}kN/m³ | c: {self.cohesion}kPa | φ: {self.friction_angle}°")

def active_pressure_multi_layer(layers, overload):
    current_sigma_v = overload
    cumulative_force = 0

    pa_top_list = []
    pa_bottom_list = []
    
    for i, layer in enumerate(layers):
        ka = layer.active_coefficient()
        cohesion_term = layer.active_cohesion_term()

        pa_top = current_sigma_v * ka - cohesion_term
        next_sigma_v = current_sigma_v + layer.unit_weight * layer.thickness
        pa_bottom = next_sigma_v * ka - cohesion_term
        current_sigma_v = next_sigma_v

        pa_top_list.append(pa_top)
        pa_bottom_list.append(pa_bottom)
    return pa_top_list,pa_bottom_list
    
def passive_pressure_at_depth(layers, depth_excavation):
    z_top = 0.0

    for i,layer in enumerate(layers):
        z_bottom = z_top + layer.thickness

        if z_top <= depth_excavation <= z_bottom:
            pp_depth = 2 * layer.cohesion * math.sqrt(layer.passive_coefficient())

            pp_bottom = (z_bottom - depth_excavation) * layer.unit_weight * layer.passive_coefficient() + pp_depth

            pp_top = None
            if i + 1 < len(layers):
                next_layer = layers[i+1]
                kp_next = next_layer.passive_coefficient()
                pp_top = (z_bottom - depth_excavation) * next_layer.unit_weight * kp_next + 2 * next_layer.cohesion * math.sqrt(kp_next)

            return i, pp_depth, pp_bottom, pp_top
        z_top = z_bottom

def find_critical_depth(layers, pa_top_list, pa_bottom_list, overload):
    current_sigma_v = overload
    cumulative_height = 0.0
    critical_depths = []

    for i, layer in enumerate(layers):
        p_top = pa_top_list[i]
        p_bottom = pa_bottom_list[i]

        if p_top * p_bottom <= 0:
            ka = layer.active_coefficient()
            c_term = layer.active_cohesion_term()
            
            delta_z = ((c_term / ka) - current_sigma_v) / layer.unit_weight
            absolute_z = cumulative_height + delta_z
                
            critical_depths.append({
                "layer_name": layer.name,
                "delta_z": round(delta_z, 4),
                "absolute_z": round(absolute_z, 4)
            })

        current_sigma_v += layer.unit_weight * layer.thickness
        cumulative_height += layer.thickness

    return critical_depths

def find_layer_at_depth(layers, target_depth):

    cumulative_h = 0.0
    
    for i, layer in enumerate(layers):
        if cumulative_h <= target_depth < (cumulative_h + layer.thickness):
            relative_depth = target_depth - cumulative_h
            return {
                'index': i,
                'relative_depth': round(relative_depth, 3),
                'top_depth': round(cumulative_h, 3)
            }
        
        cumulative_h += layer.thickness
    
    if abs(target_depth - cumulative_h) < 1e-6:
        return {
            'index': len(layers) - 1,
            'layer': layers[-1],
            'relative_depth': layers[-1].thickness,
            'top_depth': cumulative_h - layers[-1].thickness
        }

    return None

def find_inflection_point(pp_depth, pp_bottom, pa_top, pa_bottom, depth_excavation):
    if pp_depth > pa_top and pp_bottom > pa_bottom:
        return 1.2 * depth_excavation

def active_pressure_at_inflection_point(layers, inflection_point_depth, overload):
    cumulative_h = 0.0
    current_sigma_v = overload
    
    for i, layer in enumerate(layers):
        layer_bottom_depth = cumulative_h + layer.thickness
        if cumulative_h <= inflection_point_depth <= layer_bottom_depth:
            dz = inflection_point_depth - cumulative_h
            
            sigma_z = current_sigma_v + layer.unit_weight * dz
            
            ka = layer.active_coefficient()
            c_term = layer.active_cohesion_term()
            
            pa_at_depth = sigma_z * ka - c_term
            
            return max(0, pa_at_depth)
        
        current_sigma_v += layer.unit_weight * layer.thickness
        cumulative_h = layer_bottom_depth


def passive_pressure_at_inflection_point(layers, inflection_point_depth, excavation_depth):

    dz_from_excavation = inflection_point_depth - excavation_depth
    
    cumulative_h = 0.0

    current_sigma_v_passive = 0.0 
    
    for i, layer in enumerate(layers):
        layer_bottom_depth = cumulative_h + layer.thickness
        
        if cumulative_h <= inflection_point_depth <= layer_bottom_depth:

            dz_in_layer = inflection_point_depth - cumulative_h
            
            sigma_v_p = 0.0
            temp_h = 0.0
            for j in range(len(layers)):
                l = layers[j]
                l_top = temp_h
                l_bot = temp_h + l.thickness
                
                overlap_top = max(excavation_depth, l_top)
                overlap_bot = min(inflection_point_depth, l_bot)
                
                if overlap_bot > overlap_top:
                    sigma_v_p += (overlap_bot - overlap_top) * l.unit_weight
                
                temp_h = l_bot
                if temp_h >= inflection_point_depth:
                    break

            kp = layer.passive_coefficient()
            cp_term = layer.passive_cohesion_term()
            
            pp_inflection_point = sigma_v_p * kp + cp_term
            
            return pp_inflection_point
        
        cumulative_h = layer_bottom_depth
    
        
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

    print(f"{'土层名称':<20} | {'内摩擦角(°)':<10} | {'Ka (主动)':<12} | {'Kp (被动)':<12} | {'2cKa^1/2:<12'} | {'2cKp^1/2:<12'} |")
    print("-" * 55)

    for layer in layers:
        ka = layer.active_coefficient()
        kp = layer.passive_coefficient()

        ka_2 = layer.active_cohesion_term()
        kp_2 = layer.passive_cohesion_term()
        print(f"{layer.name:<20} | {layer.friction_angle:<10} | {ka:<12.1f} | {kp:<12.1f} | {ka_2:<12.2f} |{kp_2:<12.2f}")

    # 计算主动土压力
    overload = 30.0             # 地面超载
    pa_top_list, pa_bottom_list = active_pressure_multi_layer(layers, overload)
    print(pa_top_list)
    
    # 计算被动土压力
    depth_excavation = 8.5
    i, pp_depth, pp_bottom, pp_top = passive_pressure_at_depth(layers, depth_excavation)
    print(f"深度{depth_excavation}m 的被动土压力为 {pp_depth:.3f}")
    print(f"深度{depth_excavation}m 下土层底部的被动土压力为 {pp_bottom:.3f}")
    print(f"深度{depth_excavation}m 下土层顶部的被动土压力为 {pp_top:.3f}")

    # 计算临界深度
    result_critial_depth = find_critical_depth(layers, pa_top_list, pa_bottom_list, overload)
    print(result_critial_depth)

    # 开挖深度所在土层
    layer_at_depth = find_layer_at_depth(layers, depth_excavation)
    layer_index = layer_at_depth['index']
    print(layer_at_depth)
    # 计算反弯点
    depth_inflection_point = find_inflection_point(pp_depth, pp_bottom, pa_top_list[layer_index], pa_bottom_list[layer_index], depth_excavation)
    print(depth_inflection_point)
    pa_inflection_point = active_pressure_at_inflection_point(layers, depth_inflection_point, overload)
    print(pa_inflection_point)
    pp_inflection_point = passive_pressure_at_inflection_point(layers, depth_inflection_point, depth_excavation)
    print(pp_inflection_point)
    
