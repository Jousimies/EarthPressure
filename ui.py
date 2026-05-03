import tkinter as tk
from tkinter import ttk, messagebox

class SoilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("基坑土压力计算 v1.0")
        self.root.geometry("850x600") # 设置默认窗口大小
        self.layers = [] 

        # --- 1. 基本参数区 ---
        header_frame = tk.LabelFrame(root, text=" 1. 工程全局参数 ", padx=10, pady=10)
        header_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(header_frame, text="开挖深度 H (m):").grid(row=0, column=0, sticky="w")
        self.excavation_depth_entry = tk.Entry(header_frame, width=15)
        self.excavation_depth_entry.grid(row=0, column=1, padx=10)
        
        tk.Label(header_frame, text="地表超载 q (kPa):").grid(row=0, column=2, sticky="w")
        self.overload_entry = tk.Entry(header_frame, width=15)
        self.overload_entry.insert(0, "0") # 默认值 0
        self.overload_entry.grid(row=0, column=3, padx=10)

        # --- 2. 土层输入区 ---
        input_frame = tk.LabelFrame(root, text=" 2. 添加土层参数 ", padx=10, pady=10)
        input_frame.pack(fill="x", padx=15, pady=5)

        # 标签定义
        col_tags = ["名称", "厚度(m)", "重度(kN/m³)", "粘聚力c(kPa)", "摩擦角φ(°)", "水土计算"]
        for i, tag in enumerate(col_tags):
            tk.Label(input_frame, text=tag, font=("微软雅黑", 9, "bold")).grid(row=0, column=i, pady=5)
            
        # 输入控件
        self.name_ent = tk.Entry(input_frame, width=12)
        self.thick_ent = tk.Entry(input_frame, width=10)
        self.gamma_ent = tk.Entry(input_frame, width=10) # 重度输入
        self.cohesion_ent = tk.Entry(input_frame, width=10)
        self.phi_ent = tk.Entry(input_frame, width=10)
        self.calc_mode = ttk.Combobox(input_frame, values=["水土合算", "水土分算"], width=10, state="readonly")
        self.calc_mode.current(0)

        self.name_ent.grid(row=1, column=0, padx=2)
        self.thick_ent.grid(row=1, column=1, padx=2)
        self.gamma_ent.grid(row=1, column=2, padx=2)
        self.cohesion_ent.grid(row=1, column=3, padx=2)
        self.phi_ent.grid(row=1, column=4, padx=2)
        self.calc_mode.grid(row=1, column=5, padx=2)

        # 按钮颜色修正：使用标准的 'SystemButtonFace' 或明确的颜色
        self.add_btn = tk.Button(input_frame, text="添加此层", command=self.add_layer, 
                                 bg="#f0f0f0", activebackground="#dcdcdc", width=10)
        self.add_btn.grid(row=1, column=6, padx=10)

        # --- 3. 列表展示区 ---
        list_frame = tk.LabelFrame(root, text=" 3. 土层列表（自上而下） ", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("name", "thick", "gamma", "c", "phi", "mode")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 定义表头
        headings = {"name": "名称", "thick": "厚度", "gamma": "重度", "c": "粘聚力", "phi": "摩擦角", "mode": "水土计算"}
        for col, text in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        # --- 4. 提交计算按钮 ---
        # 修正颜色：绿色背景 #228B22 (ForestGreen)，白色文字
        self.submit_btn = tk.Button(root, text="确 认 并 开 始 计 算", command=self.submit_data, 
                                   bg="ForestGreen", fg="black", 
                                   activebackground="DarkGreen", activeforeground="white",
                                   font=("微软雅黑", 12, "bold"), pady=8)
        self.submit_btn.pack(fill="x", padx=15, pady=15)

    def add_layer(self):
        try:
            name = self.name_ent.get()
            thick = float(self.thick_ent.get())
            gamma = float(self.gamma_ent.get())
            c = float(self.cohesion_ent.get())
            phi = float(self.phi_ent.get())
            mode = self.calc_mode.get()

            if not name: raise ValueError("名称不能为空")
            
            data = (name, thick, gamma, c, phi, mode)
            self.layers.append(data)
            self.tree.insert("", "end", values=data)
            
            # 清空
            for ent in [self.name_ent, self.thick_ent, self.gamma_ent, self.cohesion_ent, self.phi_ent]:
                ent.delete(0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("格式错误", f"请输入正确的数值参数！\n错误提示: {e}")

    def submit_data(self):
        if not self.layers:
            messagebox.showwarning("提示", "请先添加土层信息")
            return
        try:
            h_total = float(self.excavation_depth_entry.get())
            q = float(self.overload_entry.get())
            
            # 准备传递给计算引擎的数据
            messagebox.showinfo("准备就绪", f"开挖深度：{h_total}m\n土层总数：{len(self.layers)}\n开始调用计算引擎...")
            # 在这里实例化你的 SoilLayer 对象并运行之前的计算函数
            
        except ValueError:
            messagebox.showerror("错误", "开挖深度和超载必须为有效数字")

if __name__ == "__main__":
    root = tk.Tk()
    # 设置全窗口字体
    default_font = ("微软雅黑", 9)
    root.option_add("*Font", default_font)
    app = SoilApp(root)
    root.mainloop()
