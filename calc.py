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
        phi_rad = math.radians(self.friction_angle)
        ka_2 = 2 * layer.cohesion * math.sqrt((math.tan(math.pi/4 - phi_rad/2)) ** 2)
        return ka_2
    
    def passive_coefficient(self):
        """被动土压力系数 Kp"""
        phi_rad = math.radians(self.friction_angle)
        kp = (math.tan(math.pi/4 + phi_rad/2)) ** 2
        return kp

    def passive_cohesion_term(self):
        kp_2 = 2 * layer.cohesion * round(math.sqrt(self.passive_coefficient()), 3)
        return kp_2

def passive_pressure_at_depth(layers, depth):
    z_top = 0.0

    for i,layer in enumerate(layers):
        z_bottom = z_top + layer.thickness
        #print(z_bottom)

        if z_top <= depth <= z_bottom:
            pp_depth = 2 * layer.cohesion * math.sqrt(layer.passive_coefficient())

            pp_bottom = (z_bottom - depth) * layer.unit_weight * layer.passive_coefficient() + pp_depth

            pp_top = None
            if i + 1 < len(layers):
                next_layer = layers[i+1]
                kp_next = next_layer.passive_coefficient()
                pp_top = (z_bottom - depth) * next_layer.unit_weight * kp_next + 2 * next_layer.cohesion * math.sqrt(kp_next)

            return i, pp_depth, pp_bottom, pp_top
        z_top = z_bottom


    
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

    # 计算被动土压力
    depth = 8.5
    i, pp_depth, pp_bottom, pp_top = passive_pressure_at_depth(layers, depth)
    print(f"深度{depth}m 的被动土压力为 {pp_depth:.3f}")
    print(f"深度{depth}m 下土层底部的被动土压力为 {pp_bottom:.3f}")
    print(f"深度{depth}m 下土层顶部的被动土压力为 {pp_top:.3f}")

