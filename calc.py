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
