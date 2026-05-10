import tkinter as tk
from tkinter import messagebox, ttk

from calc2 import (
    DEFAULT_CONSTRUCTION_STAGES,
    DEFAULT_PILE_TOP_Z,
    analyze_scenario_dataset,
    build_default_result_datasets,
    build_default_scenarios,
)


class ResultViewer(tk.Toplevel):
    MIN_CANVAS_WIDTH = 620
    TOP_MARGIN = 44
    BOTTOM_MARGIN = 32
    MIN_LAYER_HEIGHT = 38
    MIN_THICKNESS_EPSILON = 1e-6
    PRESSURE_LABEL_OFFSET = 10
    PASSIVE_PRESSURE_COLOR = "#1D4ED8"
    ACTIVE_PRESSURE_COLOR = "#D62828"
    LAYER_COLORS = [
        "#F4D06F",
        "#FF9B85",
        "#B8E0D2",
        "#A9DEF9",
        "#E4C1F9",
        "#CDE7BE",
        "#FFD6A5",
        "#D0F4DE",
    ]

    def __init__(self, master, datasets):
        super().__init__(master)
        self.title("土层结果展示")
        self.geometry("1240x860")
        self.minsize(1080, 760)
        self.datasets = datasets
        self.current_dataset_index = 0
        self.current_stage_index = 0

        self.dataset_title_var = tk.StringVar()
        self.dataset_meta_var = tk.StringVar()
        self.stage_summary_var = tk.StringVar()
        self.warning_var = tk.StringVar()

        self._build_layout()
        self.select_dataset(0)

    def _build_layout(self):
        selector_frame = tk.LabelFrame(self, text="结果切换", padx=10, pady=8)
        selector_frame.pack(fill="x", padx=12, pady=(12, 6))
        self.dataset_button_frame = tk.Frame(selector_frame)
        self.dataset_button_frame.pack(fill="x")

        info_frame = tk.Frame(self)
        info_frame.pack(fill="x", padx=12, pady=6)
        tk.Label(
            info_frame,
            textvariable=self.dataset_title_var,
            font=("微软雅黑", 13, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(info_frame, textvariable=self.dataset_meta_var, anchor="w").pack(fill="x", pady=(2, 0))

        stage_frame = tk.LabelFrame(self, text="工况切换", padx=8, pady=8)
        stage_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.stage_button_frame = tk.Frame(stage_frame)
        self.stage_button_frame.pack(fill="x")

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        left_frame = tk.Frame(paned)
        right_frame = tk.LabelFrame(paned, text="土层示意图", padx=8, pady=8)
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=1)

        layer_data_frame = tk.LabelFrame(left_frame, text="土层数据", padx=8, pady=8)
        layer_data_frame.pack(fill="both", expand=True)

        layer_columns = ("index", "name", "thickness", "gamma", "c", "phi", "mode", "depth")
        self.layer_tree = ttk.Treeview(layer_data_frame, columns=layer_columns, show="headings", height=14)
        layer_headings = {
            "index": "序号",
            "name": "名称",
            "thickness": "厚度(m)",
            "gamma": "重度(kN/m³)",
            "c": "粘聚力(kPa)",
            "phi": "摩擦角(°)",
            "mode": "水土计算",
            "depth": "深度范围(m)",
        }
        widths = {"index": 50, "name": 120, "thickness": 80, "gamma": 100, "c": 95, "phi": 90, "mode": 90, "depth": 110}
        for column, title in layer_headings.items():
            self.layer_tree.heading(column, text=title)
            self.layer_tree.column(column, width=widths[column], anchor="center")
        layer_scroll = ttk.Scrollbar(layer_data_frame, orient="vertical", command=self.layer_tree.yview)
        self.layer_tree.configure(yscrollcommand=layer_scroll.set)
        self.layer_tree.pack(side="left", fill="both", expand=True)
        layer_scroll.pack(side="right", fill="y")

        summary_frame = tk.LabelFrame(left_frame, text="当前工况结果", padx=8, pady=8)
        summary_frame.pack(fill="x", pady=(6, 6))
        tk.Label(summary_frame, textvariable=self.stage_summary_var, justify="left", anchor="w").pack(fill="x")
        tk.Label(summary_frame, textvariable=self.warning_var, fg="#B23A48", justify="left", anchor="w").pack(
            fill="x", pady=(4, 0)
        )

        pressure_paned = ttk.PanedWindow(left_frame, orient="horizontal")
        pressure_paned.pack(fill="both", expand=True)
        active_frame = tk.LabelFrame(pressure_paned, text="主动土压力分段", padx=8, pady=8)
        passive_frame = tk.LabelFrame(pressure_paned, text="被动土压力分段", padx=8, pady=8)
        pressure_paned.add(active_frame, weight=1)
        pressure_paned.add(passive_frame, weight=1)

        pressure_columns = ("range", "force", "centroid")
        self.active_tree = self._build_pressure_tree(active_frame, pressure_columns)
        self.passive_tree = self._build_pressure_tree(passive_frame, pressure_columns)

        self.canvas = tk.Canvas(right_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _build_pressure_tree(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=8)
        tree.heading("range", text="区间(m)")
        tree.heading("force", text="合力(kN/m)")
        tree.heading("centroid", text="形心深度(m)")
        tree.column("range", width=130, anchor="center")
        tree.column("force", width=120, anchor="center")
        tree.column("centroid", width=120, anchor="center")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def select_dataset(self, dataset_index):
        self.current_dataset_index = dataset_index
        self.current_stage_index = 0
        self._render_dataset_buttons()
        self._render_stage_buttons()
        self._refresh_dataset_view()

    def select_stage(self, stage_index):
        self.current_stage_index = stage_index
        self._render_stage_buttons()
        self._refresh_stage_view()

    def _render_dataset_buttons(self):
        for child in self.dataset_button_frame.winfo_children():
            child.destroy()

        for index, dataset in enumerate(self.datasets):
            button = tk.Button(
                self.dataset_button_frame,
                text=dataset["name"],
                command=lambda value=index: self.select_dataset(value),
                bg="#2F6690" if index == self.current_dataset_index else "#E8EEF2",
                fg="white" if index == self.current_dataset_index else "#22333B",
                relief="sunken" if index == self.current_dataset_index else "raised",
                padx=12,
                pady=4,
            )
            button.pack(side="left", padx=4, pady=2)

    def _render_stage_buttons(self):
        for child in self.stage_button_frame.winfo_children():
            child.destroy()

        dataset = self.datasets[self.current_dataset_index]
        for index, stage in enumerate(dataset["stages"]):
            button = tk.Button(
                self.stage_button_frame,
                text=stage["label"],
                command=lambda value=index: self.select_stage(value),
                bg="#3A7D44" if index == self.current_stage_index else "#F3F4F6",
                fg="white" if index == self.current_stage_index else "#1F2933",
                relief="sunken" if index == self.current_stage_index else "raised",
                padx=10,
                pady=3,
            )
            button.pack(side="left", padx=4, pady=2)

    def _refresh_dataset_view(self):
        dataset = self.datasets[self.current_dataset_index]
        self.dataset_title_var.set(dataset["name"])
        self.dataset_meta_var.set(
            f"地表超载 q = {dataset['overload']} kPa    |    桩顶高度 = {dataset['pile_top_z']} m    |    土层数 = {len(dataset['layers'])}"
        )

        for item in self.layer_tree.get_children():
            self.layer_tree.delete(item)
        for layer in dataset["layers"]:
            self.layer_tree.insert(
                "",
                "end",
                values=(
                    layer["index"],
                    layer["name"],
                    f"{layer['thickness']:.2f}",
                    f"{layer['unit_weight']:.2f}",
                    f"{layer['cohesion']:.2f}",
                    f"{layer['friction_angle']:.2f}",
                    layer["mode"],
                    f"{layer['top_depth']:.2f} ~ {layer['bottom_depth']:.2f}",
                ),
            )

        self._refresh_stage_view()

    def _refresh_stage_view(self):
        dataset = self.datasets[self.current_dataset_index]
        stage = dataset["stages"][self.current_stage_index]
        strut_position = "-" if stage["strut_depth"] is None else f"{stage['strut_depth']:.2f} m"

        critical_depths = "、".join(f"{point['z']:.2f}m" for point in stage["critical_points"]) or "无"
        inflection_depth = "未识别"
        if stage["inflection_point"] is not None:
            inflection_depth = f"{stage['inflection_point']['z']:.2f}m"
        strut_force = "未计算"
        if stage["strut_force"] is not None:
            strut_force = f"{stage['strut_force']:.2f} kN/m"

        self.stage_summary_var.set(
            "\n".join(
                [
                    f"开挖深度：{stage['excavation_depth']:.2f} m",
                    f"支撑位置：{strut_position}",
                    f"反弯点：{inflection_depth}",
                    f"临界深度：{critical_depths}",
                    f"支撑轴力：{strut_force}",
                ]
            )
        )
        self.warning_var.set("\n".join(stage["warnings"]) if stage["warnings"] else "")

        self._populate_pressure_tree(self.active_tree, stage["pressure_report"]["active"])
        self._populate_pressure_tree(self.passive_tree, stage["pressure_report"]["passive"])
        self._draw_schematic(dataset, stage)

    def _populate_pressure_tree(self, tree, items):
        for item in tree.get_children():
            tree.delete(item)

        if not items:
            tree.insert("", "end", values=("无", "-", "-"))
            return

        for item in items:
            tree.insert(
                "",
                "end",
                values=(item["range"], f"{item['force']:.2f}", f"{item['centroid_depth']:.2f}"),
            )

    def _build_layer_layout(self, layers, top_margin, usable_height):
        """按土层厚度生成缩放后的垂向布局，并保证每层最小可视高度。"""
        layer_count = len(layers)
        if layer_count == 0:
            return []

        min_height = self.MIN_LAYER_HEIGHT
        base_height = min_height * layer_count
        total_thickness = sum(self._get_safe_thickness(layer) for layer in layers)
        if total_thickness <= 0:
            # 当输入厚度全部异常时采用平均分配，避免除零并保持图形可读性。
            total_thickness = float(layer_count)

        if base_height < usable_height:
            extra_height = usable_height - base_height
            layer_heights = [min_height + extra_height * (self._get_safe_thickness(layer) / total_thickness) for layer in layers]
        else:
            equal_height = usable_height / layer_count
            layer_heights = [equal_height for _ in layers]

        layout = []
        current_y = top_margin
        for layer, layer_height in zip(layers, layer_heights):
            y1 = current_y
            y2 = current_y + layer_height
            layout.append(
                {
                    "layer": layer,
                    "top_depth": layer["top_depth"],
                    "bottom_depth": layer["bottom_depth"],
                    "y1": y1,
                    "y2": y2,
                }
            )
            current_y = y2
        return layout

    def _depth_to_canvas_y(self, depth, layer_layout, top_margin, bottom_y):
        """将真实深度映射到缩放后示意图的画布 Y 坐标。"""
        if not layer_layout:
            return top_margin
        if depth <= layer_layout[0]["top_depth"]:
            return layer_layout[0]["y1"]
        if depth >= layer_layout[-1]["bottom_depth"]:
            return bottom_y

        for item in layer_layout:
            if item["top_depth"] <= depth <= item["bottom_depth"]:
                thickness = max(item["bottom_depth"] - item["top_depth"], self.MIN_THICKNESS_EPSILON)
                ratio = (depth - item["top_depth"]) / thickness
                return item["y1"] + (item["y2"] - item["y1"]) * ratio
        return bottom_y

    def _get_safe_thickness(self, layer):
        """返回非负厚度，避免异常输入导致布局计算错误。"""
        return max(layer["thickness"], 0.0)

    def _layer_pressure_preview(self, points, layer):
        """提取该土层内的代表性被动/主动压力峰值用于示意标注。"""
        active_pressure_values = []
        passive_pressure_values = []
        for point in points:
            if point["layer_name"] != layer["name"]:
                continue
            if not (layer["top_depth"] <= point["z"] <= layer["bottom_depth"]):
                continue
            active_pressure_values.append(point["pa"])
            passive_pressure_values.append(point["pp"])
        max_passive_pressure = max(passive_pressure_values) if passive_pressure_values else 0.0
        max_active_pressure = max(active_pressure_values) if active_pressure_values else 0.0
        return max_passive_pressure, max_active_pressure

    def _draw_schematic(self, dataset, stage):
        self.canvas.delete("all")
        self.canvas.update_idletasks()

        canvas_width = max(self.canvas.winfo_width(), self.MIN_CANVAS_WIDTH)
        canvas_height = max(self.canvas.winfo_height(), 420)
        top_margin = self.TOP_MARGIN
        bottom_margin = self.BOTTOM_MARGIN
        usable_height = canvas_height - top_margin - bottom_margin
        bottom_y = canvas_height - bottom_margin
        layer_layout = self._build_layer_layout(dataset["layers"], top_margin, usable_height)

        profile_left = 220
        profile_right = canvas_width - 40
        center_x = (profile_left + profile_right) / 2

        self.canvas.create_text(center_x, 18, text="土层压力示意（左被动｜右主动）", font=("微软雅黑", 11, "bold"))
        self.canvas.create_text(
            center_x - 120,
            32,
            text="被动土压力 Pp",
            fill=self.PASSIVE_PRESSURE_COLOR,
            font=("微软雅黑", 9, "bold"),
        )
        self.canvas.create_text(
            center_x + 120,
            32,
            text="主动土压力 Pa",
            fill=self.ACTIVE_PRESSURE_COLOR,
            font=("微软雅黑", 9, "bold"),
        )

        self.canvas.create_line(profile_left, top_margin, profile_left, bottom_y, width=1, fill="#64748B")
        self.canvas.create_line(profile_right, top_margin, profile_right, bottom_y, width=1, fill="#64748B")
        self.canvas.create_line(center_x, top_margin, center_x, bottom_y, width=3, fill="#111827")
        self.canvas.create_text((profile_left + center_x) / 2, top_margin + 14, text="被动区", fill="#1E3A8A", font=("微软雅黑", 9, "bold"))
        self.canvas.create_text((center_x + profile_right) / 2, top_margin + 14, text="主动区", fill="#9A3412", font=("微软雅黑", 9, "bold"))

        points = stage.get("points", [])
        for index, item in enumerate(layer_layout):
            layer = item["layer"]
            y1 = item["y1"]
            y2 = item["y2"]
            label_y = (y1 + y2) / 2
            color = self.LAYER_COLORS[index % len(self.LAYER_COLORS)]

            self.canvas.create_rectangle(profile_left, y1, center_x, y2, fill="#DDEFFF", outline="#4A4E69")
            self.canvas.create_rectangle(center_x, y1, profile_right, y2, fill="#FFE8DD", outline="#4A4E69")
            self.canvas.create_line(profile_left, y1, profile_right, y1, fill=color, width=2)

            self.canvas.create_text(
                profile_left - 14,
                label_y,
                text=f"{layer['name']}\n{layer['thickness']:.2f}m ({layer['top_depth']:.1f}-{layer['bottom_depth']:.1f}m)",
                anchor="e",
                width=150,
                font=("微软雅黑", 9),
            )

            max_passive_pressure, max_active_pressure = self._layer_pressure_preview(points, layer)
            self.canvas.create_text(
                center_x - self.PRESSURE_LABEL_OFFSET,
                label_y,
                text=f"Pp≈{max_passive_pressure:.1f}",
                anchor="e",
                fill=self.PASSIVE_PRESSURE_COLOR,
                font=("微软雅黑", 9),
            )
            self.canvas.create_text(
                center_x + self.PRESSURE_LABEL_OFFSET,
                label_y,
                text=f"Pa≈{max_active_pressure:.1f}",
                anchor="w",
                fill=self.ACTIVE_PRESSURE_COLOR,
                font=("微软雅黑", 9),
            )

            self.canvas.create_text(profile_left - 166, y1, text=f"{layer['top_depth']:.1f}m", anchor="e", fill="#475569")

        if layer_layout:
            self.canvas.create_text(
                profile_left - 166,
                layer_layout[-1]["y2"],
                text=f"{layer_layout[-1]['bottom_depth']:.1f}m",
                anchor="e",
                fill="#475569",
            )

        self._draw_depth_marker(profile_left, profile_right, layer_layout, top_margin, bottom_y, stage["excavation_depth"], "#D62828", "开挖面")

        if stage["strut_depth"] is not None:
            y = self._depth_to_canvas_y(stage["strut_depth"], layer_layout, top_margin, bottom_y)
            self.canvas.create_line(center_x, y, profile_right - 8, y, fill="#1D4ED8", width=3)
            self.canvas.create_oval(profile_right - 14, y - 5, profile_right - 4, y + 5, fill="#1D4ED8", outline="")
            self.canvas.create_text(profile_right - 2, y, text=f"支撑 {stage['strut_depth']:.2f}m", anchor="w", fill="#1D4ED8")

        if stage["inflection_point"] is not None:
            self._draw_depth_marker(
                profile_left,
                profile_right,
                layer_layout,
                top_margin,
                bottom_y,
                stage["inflection_point"]["z"],
                "#7B2CBF",
                "反弯点",
            )

        for point in stage["critical_points"]:
            self._draw_depth_marker(
                profile_left,
                profile_right,
                layer_layout,
                top_margin,
                bottom_y,
                point["z"],
                "#FF8800",
                "临界点",
                offset=20,
            )

    def _draw_depth_marker(self, left, right, layer_layout, top_margin, bottom_y, depth, color, label, offset=0):
        y = self._depth_to_canvas_y(depth, layer_layout, top_margin, bottom_y)
        self.canvas.create_line(left - 10, y, right + 10, y, fill=color, width=2, dash=(6, 4))
        self.canvas.create_text(right + 20 + offset, y, text=f"{label} {depth:.2f}m", anchor="w", fill=color)


class SoilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("基坑土压力计算 v2.0")
        self.root.geometry("980x720")
        self.layers = []
        self.example_scenarios = build_default_scenarios()

        self._build_layout()

    def _build_layout(self):
        header_frame = tk.LabelFrame(self.root, text="1. 工程全局参数", padx=10, pady=10)
        header_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(header_frame, text="开挖深度 H (m):").grid(row=0, column=0, sticky="w", padx=5)
        self.excavation_depth_entry = tk.Entry(header_frame, width=12)
        self.excavation_depth_entry.grid(row=0, column=1, padx=5)

        tk.Label(header_frame, text="地表超载 q (kPa):").grid(row=0, column=2, sticky="w", padx=5)
        self.overload_entry = tk.Entry(header_frame, width=12)
        self.overload_entry.insert(0, "0")
        self.overload_entry.grid(row=0, column=3, padx=5)

        tk.Label(header_frame, text="桩顶高度 (m):").grid(row=0, column=4, sticky="w", padx=5)
        self.pile_depth_entry = tk.Entry(header_frame, width=12)
        self.pile_depth_entry.insert(0, str(DEFAULT_PILE_TOP_Z))
        self.pile_depth_entry.grid(row=0, column=5, padx=5)

        example_frame = tk.LabelFrame(self.root, text="2. 示例土层快速加载", padx=10, pady=10)
        example_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(example_frame, text="选择截面:").pack(side="left", padx=(0, 6))
        self.example_selector = ttk.Combobox(
            example_frame,
            values=[scenario["name"] for scenario in self.example_scenarios],
            state="readonly",
            width=18,
        )
        self.example_selector.current(0)
        self.example_selector.pack(side="left", padx=4)
        tk.Button(example_frame, text="载入到输入区", command=self.load_example_layers).pack(side="left", padx=8)
        tk.Button(example_frame, text="仅查看示例结果", command=self.open_default_results).pack(side="left", padx=8)

        input_frame = tk.LabelFrame(self.root, text="3. 添加土层参数", padx=10, pady=10)
        input_frame.pack(fill="x", padx=15, pady=5)

        col_tags = ["名称", "厚度(m)", "重度(kN/m³)", "粘聚力c(kPa)", "摩擦角φ(°)", "水土计算"]
        for index, tag in enumerate(col_tags):
            tk.Label(input_frame, text=tag, font=("微软雅黑", 9, "bold")).grid(row=0, column=index, pady=5)

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

        tk.Button(input_frame, text="添加此层", command=self.add_layer, width=10).grid(row=1, column=6, padx=10)
        tk.Button(input_frame, text="删除选中层", command=self.remove_selected_layer, width=10).grid(row=1, column=7, padx=4)
        tk.Button(input_frame, text="清空全部", command=self.clear_layers, width=10).grid(row=1, column=8, padx=4)

        list_frame = tk.LabelFrame(self.root, text="4. 土层列表（自上而下）", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("name", "thick", "gamma", "c", "phi", "mode")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        headings = {
            "name": "名称",
            "thick": "厚度(m)",
            "gamma": "重度(kN/m³)",
            "c": "粘聚力(kPa)",
            "phi": "摩擦角(°)",
            "mode": "水土计算",
        }
        for col, text in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=130, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.submit_btn = tk.Button(
            self.root,
            text="确认并计算 + 打开结果界面",
            command=self.submit_data,
            bg="ForestGreen",
            fg="white",
            activebackground="DarkGreen",
            activeforeground="white",
            font=("微软雅黑", 12, "bold"),
            pady=10,
        )
        self.submit_btn.pack(fill="x", padx=15, pady=15)

    def add_layer(self):
        try:
            layer = {
                "name": self.name_ent.get().strip(),
                "thickness": float(self.thick_ent.get()),
                "unit_weight": float(self.gamma_ent.get()),
                "cohesion": float(self.cohesion_ent.get()),
                "friction_angle": float(self.phi_ent.get()),
                "mode": self.calc_mode.get(),
            }
            if not layer["name"]:
                raise ValueError("名称不能为空")
            if layer["thickness"] <= 0 or layer["unit_weight"] <= 0:
                raise ValueError("厚度和重度必须大于 0")

            self.layers.append(layer)
            self.tree.insert(
                "",
                "end",
                values=(
                    layer["name"],
                    f"{layer['thickness']:.2f}",
                    f"{layer['unit_weight']:.2f}",
                    f"{layer['cohesion']:.2f}",
                    f"{layer['friction_angle']:.2f}",
                    layer["mode"],
                ),
            )

            for entry in [self.name_ent, self.thick_ent, self.gamma_ent, self.cohesion_ent, self.phi_ent]:
                entry.delete(0, tk.END)
            self.name_ent.focus_set()
        except ValueError as error:
            messagebox.showerror("格式错误", f"请输入有效的土层参数。\n错误详情：{error}")

    def remove_selected_layer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选中要删除的土层。")
            return

        indices = sorted((self.tree.index(item) for item in selected), reverse=True)
        for item in selected:
            self.tree.delete(item)
        for index in indices:
            self.layers.pop(index)

    def clear_layers(self):
        self.layers.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_example_layers(self):
        scenario = self.example_scenarios[self.example_selector.current()]
        self.clear_layers()
        self.overload_entry.delete(0, tk.END)
        self.overload_entry.insert(0, str(scenario["overload"]))
        self.pile_depth_entry.delete(0, tk.END)
        self.pile_depth_entry.insert(0, str(DEFAULT_PILE_TOP_Z))

        self.excavation_depth_entry.delete(0, tk.END)
        self.excavation_depth_entry.insert(0, str(DEFAULT_CONSTRUCTION_STAGES[0]["excavation"]))

        for layer in scenario["layers"]:
            copied = dict(layer)
            copied["mode"] = copied.get("mode", "水土合算")
            self.layers.append(copied)
            self.tree.insert(
                "",
                "end",
                values=(
                    copied["name"],
                    f"{copied['thickness']:.2f}",
                    f"{copied['unit_weight']:.2f}",
                    f"{copied['cohesion']:.2f}",
                    f"{copied['friction_angle']:.2f}",
                    copied["mode"],
                ),
            )

    def open_default_results(self):
        ResultViewer(self.root, build_default_result_datasets())

    def submit_data(self):
        if not self.layers:
            messagebox.showwarning("提示", "请至少添加一个土层。")
            return

        try:
            excavation_depth = float(self.excavation_depth_entry.get())
            overload = float(self.overload_entry.get())
            pile_top_z = float(self.pile_depth_entry.get())
        except ValueError:
            messagebox.showerror("错误", "全局参数（开挖深度/超载/桩顶）必须为数字。")
            return

        if excavation_depth <= 0:
            messagebox.showerror("错误", "开挖深度必须大于 0。")
            return

        custom_dataset = analyze_scenario_dataset(
            "当前输入",
            self.layers,
            overload,
            pile_top_z=pile_top_z,
            construction_stages=[{"label": "当前工况", "excavation": excavation_depth}],
        )
        datasets = [custom_dataset] + build_default_result_datasets()
        ResultViewer(self.root, datasets)


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", ("微软雅黑", 9))
    SoilApp(root)
    root.mainloop()
