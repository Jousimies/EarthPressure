import tkinter as tk
from tkinter import ttk, messagebox

class SoilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("基坑土压力计算 v1.0")
        self.root.geometry("900x650") # 稍微调宽以容纳更多顶部参数
        self.layers = [] 

        # --- 1. 基本参数区 ---
        header_frame = tk.LabelFrame(root, text=" 1. 工程全局参数 ", padx=10, pady=10)
        header_frame.pack(fill="x", padx=15, pady=10)

        # 使用不同的 column 索引防止重叠
        tk.Label(header_frame, text="开挖深度 H (m):").grid(row=0, column=0, sticky="w", padx=5)
        self.excavation_depth_entry = tk.Entry(header_frame, width=12)
        self.excavation_depth_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(header_frame, text="地表超载 q (kPa):").grid(row=0, column=2, sticky="w", padx=5)
        self.overload_entry = tk.Entry(header_frame, width=12)
        self.overload_entry.insert(0, "0") 
        self.overload_entry.grid(row=0, column=3, padx=5)

        tk.Label(header_frame, text="桩顶高度 (m):").grid(row=0, column=4, sticky="w", padx=5)
        self.pile_depth_entry = tk.Entry(header_frame, width=12)
        self.pile_depth_entry.insert(0, "0")
        self.pile_depth_entry.grid(row=0, column=5, padx=5)

        # --- 2. 土层输入区 ---
        input_frame = tk.LabelFrame(root, text=" 2. 添加土层参数 ", padx=10, pady=10)
        input_frame.pack(fill="x", padx=15, pady=5)

        col_tags = ["名称", "厚度(m)", "重度(kN/m³)", "粘聚力c(kPa)", "摩擦角φ(°)", "水土计算"]
        for i, tag in enumerate(col_tags):
            tk.Label(input_frame, text=tag, font=("微软雅黑", 9, "bold")).grid(row=0, column=i, pady=5)
            
        self.name_ent = tk.Entry(input_frame, width=12)
        self.thick_ent = tk.Entry(input_frame, width=10)
        self.gamma_ent = tk.Entry(input_frame, width=10) 
        self.cohesion_ent = tk.Entry(input_frame, width=10)
        self.phi_ent = tk.Entry(input_frame, width=10)
        self.calc_mode = ttk.Combobox(input_frame, values=["水土合算", "水土分算"], width=12, state="readonly")
        self.calc_mode.current(0)

        self.name_ent.grid(row=1, column=0, padx=2)
        self.thick_ent.grid(row=1, column=1, padx=2)
        self.gamma_ent.grid(row=1, column=2, padx=2)
        self.cohesion_ent.grid(row=1, column=3, padx=2)
        self.phi_ent.grid(row=1, column=4, padx=2)
        self.calc_mode.grid(row=1, column=5, padx=2)

        self.add_btn = tk.Button(input_frame, text="添加此层", command=self.add_layer, 
                                 bg="#f0f0f0", activebackground="#dcdcdc", width=10)
        self.add_btn.grid(row=1, column=6, padx=10)

        # --- 3. 列表展示区 ---
        list_frame = tk.LabelFrame(root, text=" 3. 土层列表（自上而下） ", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("name", "thick", "gamma", "c", "phi", "mode")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        headings = {"name": "名称", "thick": "厚度(m)", "gamma": "重度(kN/m³)", "c": "粘聚力(kPa)", "phi": "摩擦角(°)", "mode": "水土计算"}
        for col, text in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120, anchor="center")
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 4. 提交计算按钮 ---
        # 修正：fg="white" 提高对比度
        self.submit_btn = tk.Button(root, text="确 认 并 开 始 计 算", command=self.submit_data, 
                                   bg="ForestGreen", fg="white", 
                                   activebackground="DarkGreen", activeforeground="white",
                                   font=("微软雅黑", 12, "bold"), pady=10)
        self.submit_btn.pack(fill="x", padx=15, pady=15)

    def add_layer(self):
        try:
            name = self.name_ent.get().strip()
            thick = float(self.thick_ent.get())
            gamma = float(self.gamma_ent.get())
            c = float(self.cohesion_ent.get())
            phi = float(self.phi_ent.get())
            mode = self.calc_mode.get()

            if not name: raise ValueError("名称不能为空")
            
            data = (name, f"{thick:.2f}", f"{gamma:.2f}", f"{c:.2f}", f"{phi:.2f}", mode)
            self.layers.append(data)
            self.tree.insert("", "end", values=data)
            
            # 清空输入框以便下次输入
            for ent in [self.name_ent, self.thick_ent, self.gamma_ent, self.cohesion_ent, self.phi_ent]:
                ent.delete(0, tk.END)
            self.name_ent.focus_set() # 焦点回到名称框
            
        except ValueError as e:
            messagebox.showerror("格式错误", f"请输入有效的数值！\n错误详情: {e}")

    def submit_data(self):
        if not self.layers:
            messagebox.showwarning("提示", "请至少添加一个土层！")
            return
        try:
            h_exc = float(self.excavation_depth_entry.get())
            q_over = float(self.overload_entry.get())
            p_top = float(self.pile_depth_entry.get())
            
            msg = (f"参数确认：\n"
                   f"开挖深度: {h_exc} m\n"
                   f"地表超载: {q_over} kPa\n"
                   f"桩顶高度: {p_top} m\n"
                   f"土层总数: {len(self.layers)} 层\n\n"
                   "确认开始计算吗？")
            
            if messagebox.askyesno("确认提交", msg):
                # 后面接入你的 SoilLayer 实例化逻辑和压力计算逻辑
                pass
            
        except ValueError:
            messagebox.showerror("错误", "全局参数（深度/超载/桩顶）必须为数字")

if __name__ == "__main__":
    root = tk.Tk()
    default_font = ("微软雅黑", 9)
    root.option_add("*Font", default_font)
    app = SoilApp(root)
    root.mainloop()
