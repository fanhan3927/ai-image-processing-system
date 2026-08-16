# -*- coding: utf-8 -*-
"""
AI Image Processing System（AI 图像处理系统）

基于 Tkinter + Pillow 构建的桌面应用主界面骨架。

界面布局（Frame + Grid 简洁布局）：
    - 上部：按钮区，共 8 个功能按钮（4 列 x 2 行）
    - 下部：图像显示区

当前已实现功能：
    - “打开图像”：通过文件对话框选择本地图像，
      使用 Pillow 按比例缩放以适配显示区并显示。
    - “图像灰度处理”：将当前图像转换为 8 位灰度图并显示。
    - “图像阈值化”：按用户指定阈值将图像二值化（黑白）并显示。
    - “Sobel 锐化”：用 Sobel 算子计算梯度幅值并叠加到原图，突出图像边缘。
    - “Canny 边缘检测”：高斯降噪 + Sobel 梯度 + 阈值二值化（简化版 Canny）。
    - “图像平移”：按用户输入的偏移量平移图像，空出的区域填充为黑色。
    - “直方图均衡化”：基于累计分布函数拉伸灰度范围，增强图像对比度。
    - “均值滤波”：3x3 邻域平均，平滑图像、抑制噪声。

运行依赖：Pillow（安装命令：pip install pillow）
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from typing import Callable, Tuple

from PIL import Image, ImageChops, ImageFilter, ImageTk

# 兼容不同 Pillow 版本的高质量缩放算法常量
# Pillow >= 10 推荐使用 Image.Resampling.LANCZOS，旧版本使用 Image.LANCZOS
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover - 旧版 Pillow 兼容
    RESAMPLE_LANCZOS = Image.LANCZOS

# 显示区与图像边缘之间的留白（像素）
DISPLAY_PADDING = 8

# 图像阈值化功能的默认阈值（取值 0-255）
DEFAULT_THRESHOLD: int = 128

# Sobel 算子 3x3 卷积核（X 方向 / Y 方向），用于梯度计算
# 卷积核按行优先排列：Gx 检测竖直边缘，Gy 检测水平边缘
SOBEL_KERNEL_X: Tuple[float, ...] = (-1, 0, 1, -2, 0, 2, -1, 0, 1)
SOBEL_KERNEL_Y: Tuple[float, ...] = (-1, -2, -1, 0, 0, 0, 1, 2, 1)

# 均值滤波 3x3 卷积核（全 1，scale=9 即取 3x3 邻域像素的平均值）
MEAN_FILTER_KERNEL: Tuple[float, ...] = (1, 1, 1, 1, 1, 1, 1, 1, 1)

# Canny 边缘检测参数
CANNY_GAUSSIAN_RADIUS: float = 1.5  # 高斯模糊半径：先降噪，抑制噪声产生的伪边缘
DEFAULT_CANNY_THRESHOLD: int = 100  # 边缘强度阈值（0-255），越大检测到的边缘越少


class ImageApp:
    """AI 图像处理系统主界面。

    负责构建主窗口、按钮区与图像显示区，
    并提供“打开图像”及各类图像处理功能的入口回调。
    新增图像处理功能时，只需在 ``_build_button_area`` 中注册
    新的 (按钮文本, 回调方法)，并在对应回调中实现算法即可。
    """

    # ---------------- 界面常量 ----------------
    WINDOW_TITLE: str = "AI Image Processing System"
    WINDOW_SIZE: str = "900x650"
    MIN_WINDOW_SIZE: str = "640x480"
    DISPLAY_BG: str = "#2b2b2b"        # 显示区背景色（深灰）
    PLACEHOLDER_TEXT: str = "请点击「打开图像」选择一张图片"

    # 文件对话框允许选择的图像格式
    FILE_TYPES: Tuple[Tuple[str, str], ...] = (
        ("图像文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
        ("所有文件", "*.*"),
    )

    def __init__(self, root: tk.Tk) -> None:
        """初始化主窗口及内部状态。"""
        self.root = root
        root.title(self.WINDOW_TITLE)
        root.geometry(self.WINDOW_SIZE)
        root.minsize(*map(int, self.MIN_WINDOW_SIZE.split("x")))

        # ---------------- 内部状态 ----------------
        self._original_image: Image.Image | None = None      # 当前工作图像（最近打开的原图，或处理后的结果）
        self._display_image: Image.Image | None = None       # 按显示区缩放后的图像
        self._photo: ImageTk.PhotoImage | None = None        # 界面显示的 PhotoImage（必须持有引用，防止被 GC 回收）
        self._last_fit_size: Tuple[int, int] = (0, 0)        # 上次缩放所用尺寸，用于避免重复缩放
        self._last_display_image: Image.Image | None = None  # 上次显示的图像对象，用于判断是否需要重绘

        # ---------------- 构建界面 ----------------
        self._build_layout()

    # ================================================================
    # 界面构建
    # ================================================================
    def _build_layout(self) -> None:
        """构建整体布局：根窗口第 0 行为按钮区，第 1 行为图像显示区。"""
        self.root.rowconfigure(0, weight=0)  # 按钮区固定高度
        self.root.rowconfigure(1, weight=1)  # 显示区占据剩余空间
        self.root.columnconfigure(0, weight=1)

        self._build_button_area()
        self._build_display_area()

    def _build_button_area(self) -> None:
        """构建上部按钮区：8 个功能按钮，4 列 x 2 行 Grid 布局。

        按钮与其回调方法在此集中注册，新增功能时在此追加即可。
        """
        self._button_frame = tk.Frame(self.root)
        self._button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # 4 列等宽，按钮随窗口横向拉伸
        for col in range(4):
            self._button_frame.columnconfigure(col, weight=1)

        # (按钮文本, 回调方法) —— 顺序即界面展示顺序
        actions: Tuple[Tuple[str, Callable[[], None]], ...] = (
            ("打开图像", self._open_image),
            ("图像灰度处理", self._grayscale),
            ("图像平移", self._translate),
            ("图像阈值化", self._threshold),
            ("直方图均衡化", self._histogram_equalize),
            ("Sobel锐化", self._sobel_sharpen),
            ("均值滤波", self._mean_filter),
            ("Canny边缘", self._canny_edge),
        )

        for index, (text, command) in enumerate(actions):
            button = tk.Button(self._button_frame, text=text, command=command)
            button.grid(
                row=index // 4,          # 每行 4 个按钮
                column=index % 4,
                sticky="ew",
                padx=4,
                pady=4,
                ipady=3,                 # 增加按钮纵向内边距，更易点击
            )

    def _build_display_area(self) -> None:
        """构建下部图像显示区：一个带边框的 Frame，内部放置图像 Label。"""
        self._display_frame = tk.Frame(
            self.root, bg=self.DISPLAY_BG, relief=tk.SUNKEN, bd=2
        )
        self._display_frame.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=(0, 10)
        )
        self._display_frame.rowconfigure(0, weight=1)
        self._display_frame.columnconfigure(0, weight=1)

        self._image_label = tk.Label(
            self._display_frame,
            text=self.PLACEHOLDER_TEXT,
            bg=self.DISPLAY_BG,
            fg="#9e9e9e",
        )
        self._image_label.grid(row=0, column=0, sticky="nsew")

        # 窗口尺寸变化时，按新尺寸重新缩放图像以适配显示区
        self._display_frame.bind("<Configure>", self._on_display_resize)

    # ================================================================
    # 图像显示
    # ================================================================
    def _open_image(self) -> None:
        """打开图像：选择本地文件并显示（按比例缩放以适配显示区）。"""
        path = filedialog.askopenfilename(
            title="选择图像文件", filetypes=self.FILE_TYPES, parent=self.root
        )
        if not path:  # 用户取消选择
            return

        try:
            # 使用上下文管理器确保文件句柄及时关闭；
            # 先 load() 将像素数据读入内存，再 copy() 得到完全独立的图像对象。
            with Image.open(path) as image:
                image.load()
                self._original_image = image.copy()
        except Exception as exc:
            messagebox.showerror(
                "错误", f"无法打开图像：\n{path}\n\n{exc}", parent=self.root
            )
            return

        self._refresh_display()

    def _on_display_resize(self, event: tk.Event) -> None:
        """显示区尺寸变化（如拖拽窗口）时，重新缩放图像。"""
        if self._original_image is None:
            return
        self._refresh_display()

    def _refresh_display(self) -> None:
        """根据显示区当前可用尺寸，按比例缩放当前工作图像并刷新界面。"""
        image = self._original_image
        if image is None:
            return

        self.root.update_idletasks()  # 确保拿到最新的窗口/控件尺寸
        max_size = self._get_display_size()
        # 仅当“显示区尺寸”和“图像对象”都未变化时才跳过重绘：
        # 执行灰度/阈值等处理后工作图像已更换为新对象，即使尺寸相同也必须重新显示。
        if max_size == self._last_fit_size and image is self._last_display_image:
            return

        self._last_fit_size = max_size
        self._last_display_image = image
        self._display_image = self._fit_image(image, max_size)
        self._photo = ImageTk.PhotoImage(self._display_image)
        self._image_label.configure(image=self._photo, text="")

    def _get_display_size(self) -> Tuple[int, int]:
        """返回显示区中可供图像使用的最大尺寸 (宽, 高)，单位像素。"""
        width = max(self._display_frame.winfo_width() - 2 * DISPLAY_PADDING, 1)
        height = max(self._display_frame.winfo_height() - 2 * DISPLAY_PADDING, 1)
        return (width, height)

    @staticmethod
    def _fit_image(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """按比例缩放图像，使其完整适配给定的最大尺寸。

        - 图像比显示区大：等比缩小至刚好放入显示区；
        - 图像比显示区小：保持原尺寸（避免放大导致模糊）。

        参数:
            image: 原始 PIL 图像。
            max_size: 目标最大尺寸 (最大宽, 最大高)。
        返回:
            缩放后的新 PIL 图像（原始图像不会被修改）。
        """
        max_width, max_height = max_size
        width, height = image.size

        # 计算等比缩放比例：取两个方向缩放比中的较小值
        ratio = min(max_width / width, max_height / height)
        if ratio >= 1.0:
            return image

        new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))
        return image.resize(new_size, RESAMPLE_LANCZOS)

    # ================================================================
    # 图像处理功能回调
    # 全部 8 项功能均已实现：
    # 灰度处理 / 阈值化 / Sobel 锐化 / Canny 边缘 / 平移 / 直方图均衡化 / 均值滤波
    # ================================================================
    def _require_image(self) -> Image.Image | None:
        """获取当前工作图像；若尚未打开图像则给出提示并返回 None。

        返回:
            当前工作图像；未打开图像时返回 None（并弹出提示对话框）。
        """
        if self._original_image is None:
            messagebox.showinfo(
                "提示", "请先点击「打开图像」选择一张图片！", parent=self.root
            )
            return None
        return self._original_image

    def _grayscale(self) -> None:
        """图像灰度处理：将当前图像转换为 8 位灰度图并显示。

        实现方式：调用 PIL 的 convert("L")，把 RGB 等模式转为
        灰度模式（每个像素取值 0-255）；convert() 返回新图像对象，
        不会修改原图，因此可放心反复调用。
        """
        image = self._require_image()
        if image is None:
            return

        # "L" 表示 8 位灰度模式（亮度 0-255）
        self._original_image = image.convert("L")
        self._refresh_display()

    @staticmethod
    def _translate_image(image: Image.Image, dx: int, dy: int) -> Image.Image:
        """将图像整体平移 (dx, dy)，空出的区域用黑色填充。

        实现方式：新建与原图同尺寸的新图像（默认黑色背景），
        将原图粘贴到偏移 (dx, dy) 处，越界部分自动裁剪。

        参数:
            image: 待平移的图像（支持 RGB / 灰度等任意模式）。
            dx: 水平偏移量（正数向右，负数向左）。
            dy: 垂直偏移量（正数向下，负数向上）。
        返回:
            平移后的新图像（尺寸与原图一致）。
        """
        width, height = image.size
        translated = Image.new(image.mode, (width, height))  # 默认填充黑色
        translated.paste(image, (dx, dy))
        return translated

    def _translate(self) -> None:
        """图像平移：按用户输入的偏移量 (dx, dy) 平移图像并显示。"""
        image = self._require_image()
        if image is None:
            return

        dx = simpledialog.askinteger(
            "图像平移",
            "请输入水平偏移量 dx（正数向右，负数向左）：",
            initialvalue=0,
            parent=self.root,
        )
        if dx is None:  # 用户点击“取消”，不执行处理
            return
        dy = simpledialog.askinteger(
            "图像平移",
            "请输入垂直偏移量 dy（正数向下，负数向上）：",
            initialvalue=0,
            parent=self.root,
        )
        if dy is None:  # 用户点击“取消”，不执行处理
            return

        self._original_image = self._translate_image(image, dx, dy)
        self._refresh_display()

    def _threshold(self) -> None:
        """图像阈值化：按用户指定阈值将图像二值化（黑白）并显示。

        实现步骤：
        1. 弹出输入框获取阈值（0-255，默认取 DEFAULT_THRESHOLD）；
        2. 先将图像转为灰度图；
        3. 构造查找表 (Look-Up Table) 并交给 point() 逐像素处理：
           像素值大于阈值 -> 255（白色），否则 -> 0（黑色）。
        """
        image = self._require_image()
        if image is None:
            return

        threshold = simpledialog.askinteger(
            "图像阈值化",
            "请输入阈值（0-255）：像素值大于阈值的置为白色，否则置为黑色。",
            initialvalue=DEFAULT_THRESHOLD,
            minvalue=0,
            maxvalue=255,
            parent=self.root,
        )
        if threshold is None:  # 用户点击“取消”，不执行处理
            return

        gray = image.convert("L")  # 先转为灰度图，再做二值化
        # 查找表：一次性为 0-255 每个像素值指定映射结果，
        # 比在 point() 中传入 Python 函数逐像素回调更快
        lookup_table = [255 if value > threshold else 0 for value in range(256)]
        self._original_image = gray.point(lookup_table)
        self._refresh_display()

    @staticmethod
    def _equalize_histogram(gray: Image.Image) -> Image.Image:
        """对灰度图做直方图均衡化，增强图像对比度。

        算法步骤（经典直方图均衡化）：
        1. 统计灰度直方图：hist[v] = 灰度值 v（0-255）的像素个数；
        2. 计算累计分布函数 CDF[v] = sum(hist[0..v])；
        3. 构造映射查找表：new = (CDF[v] - CDF_min) / (N - CDF_min) * 255，
           其中 N 为像素总数，CDF_min 为 CDF 的最小非零值
           （即图像中最暗灰度的累计值），使均衡后的图像充分利用 0-255
           整个灰度范围；
        4. 用 point() 查找表完成逐像素映射。

        参数:
            gray: 灰度模式（"L"）的 PIL 图像。
        返回:
            均衡化后的灰度图像（尺寸不变）。
        """
        histogram = gray.histogram()  # 256 个灰度级各自的像素个数
        pixel_count = gray.width * gray.height

        # 累计分布函数 CDF
        cdf: list[int] = []
        cumulative = 0
        for count in histogram:
            cumulative += count
            cdf.append(cumulative)

        # CDF 的最小非零值（对应图像中最暗灰度的累计像素数）
        cdf_min = next((value for value in cdf if value > 0), 0)
        if pixel_count == cdf_min:
            return gray  # 常数图像（只含一个灰度级），均衡化无意义，原样返回

        # 映射查找表：将累计分布归一化并拉伸到 0-255
        lookup_table = [
            int(round((value - cdf_min) * 255 / (pixel_count - cdf_min)))
            for value in cdf
        ]
        return gray.point(lookup_table)

    def _histogram_equalize(self) -> None:
        """直方图均衡化：增强图像对比度并显示（输出为灰度图）。"""
        image = self._require_image()
        if image is None:
            return

        self._original_image = self._equalize_histogram(image.convert("L"))
        self._refresh_display()

    @staticmethod
    def _replicate_pad(image: Image.Image, pad: int = 1) -> Image.Image:
        """按“边缘像素复制”方式扩展图像四边，避免滤波在边界产生虚假梯度。

        PIL 的卷积/模糊对超出图像范围的位置按 0 填充，会在图像四周形成
        虚假的边缘响应；先把四边按边缘像素复制扩展，处理完再裁剪掉，
        即可消除该伪影（扩展区最终会被丢弃，因此近似复制即可）。

        参数:
            image: 待扩展的图像。
            pad: 每边扩展的像素数（Sobel 3x3 卷积核至少需要 1）。
        返回:
            扩展后的新图像，尺寸 = 原尺寸 + 2*pad。
        """
        width, height = image.size
        expanded = Image.new(image.mode, (width + 2 * pad, height + 2 * pad))
        expanded.paste(image, (pad, pad))  # 原图居中

        # 上 / 下扩展行：复制原图第 0 行 / 最后一行
        top_row = image.crop((0, 0, width, 1))
        bottom_row = image.crop((0, height - 1, width, height))
        for y in range(pad):
            expanded.paste(top_row, (0, y))
            expanded.paste(bottom_row, (0, height + pad + y))

        # 左 / 右扩展列：复制原图第 0 列 / 最后一列
        left_col = image.crop((0, 0, 1, height))
        right_col = image.crop((width - 1, 0, width, height))
        for x in range(pad):
            expanded.paste(left_col, (x, 0))
            expanded.paste(right_col, (width + pad + x, 0))
        return expanded

    @staticmethod
    def _sobel_magnitude(gray: Image.Image) -> Image.Image:
        """计算灰度图的 Sobel 梯度幅值（Sobel 锐化与 Canny 边缘检测共用）。

        实现思路：
        1. 先按边缘像素复制扩展 1 像素边界，避免卷积在图像四周产生虚假梯度；
        2. 梯度本身有正有负，而 PIL 卷积会把负值截断为 0（丢失方向信息）；
           因此对扩展图与其反相图（255 - 原图）分别做 Gx、Gy 卷积——
           原图卷积捕获正向梯度，反相图卷积等价捕获反向梯度，
           两者相加得到 |Gx|（|Gy| 同理）；
        3. 梯度幅值 = |Gx| + |Gy|（L1 范数近似），最后裁剪掉扩展边界。

        参数:
            gray: 灰度模式（"L"）的 PIL 图像。
        返回:
            梯度幅值图（"L" 模式，0-255，尺寸与原图一致），亮处即边缘位置。
        """
        padded = ImageApp._replicate_pad(gray, 1)   # 扩展边界（3x3 卷积核需 1 像素）
        inverted = ImageChops.invert(padded)        # 反相图：等价翻转梯度方向
        sobel_x = ImageFilter.Kernel((3, 3), SOBEL_KERNEL_X, scale=1.0)
        sobel_y = ImageFilter.Kernel((3, 3), SOBEL_KERNEL_Y, scale=1.0)
        # |Gx| = 正向 Gx + 反向 Gx（ImageChops.add 为饱和加法，越界自动截断到 255）
        abs_gx = ImageChops.add(padded.filter(sobel_x), inverted.filter(sobel_x))
        abs_gy = ImageChops.add(padded.filter(sobel_y), inverted.filter(sobel_y))
        magnitude = ImageChops.add(abs_gx, abs_gy)  # 幅值 = |Gx| + |Gy|
        # 裁剪掉扩展的 1 像素边界，恢复原图尺寸
        return magnitude.crop(
            (1, 1, magnitude.width - 1, magnitude.height - 1)
        )

    def _sobel_sharpen(self) -> None:
        """Sobel 锐化：用 Sobel 算子提取边缘强度并叠加到原图，突出图像轮廓。

        实现方式：原灰度图 + Sobel 梯度幅值，边缘处梯度大、亮度提升，
        平坦区域梯度接近 0、几乎不变（ImageChops.add 为饱和加法，
        结果自动截断到 0-255，不会溢出）。
        """
        image = self._require_image()
        if image is None:
            return

        gray = image.convert("L")  # Sobel 算子作用于灰度图
        magnitude = self._sobel_magnitude(gray)
        # 原图叠加边缘强度 = 锐化结果
        self._original_image = ImageChops.add(gray, magnitude)
        self._refresh_display()

    @staticmethod
    def _mean_filter_image(gray: Image.Image) -> Image.Image:
        """对灰度图做 3x3 均值滤波（邻域平均，平滑去噪）。

        实现方式：构造 3x3 全 1 卷积核（scale=9，即求 3x3 邻域的平均值），
        先复制扩展 1 像素边界避免卷积在四周产生虚假响应，滤波后裁剪回原尺寸。

        参数:
            gray: 灰度模式（"L"）的 PIL 图像。
        返回:
            滤波后的灰度图像（尺寸不变）。
        """
        padded = ImageApp._replicate_pad(gray, 1)
        kernel = ImageFilter.Kernel((3, 3), MEAN_FILTER_KERNEL, scale=9.0)
        filtered = padded.filter(kernel)
        # 裁剪掉扩展的 1 像素边界，恢复原图尺寸
        return filtered.crop((1, 1, filtered.width - 1, filtered.height - 1))

    def _mean_filter(self) -> None:
        """均值滤波：对图像做 3x3 均值滤波（平滑去噪）并显示（输出为灰度图）。"""
        image = self._require_image()
        if image is None:
            return

        self._original_image = self._mean_filter_image(image.convert("L"))
        self._refresh_display()

    def _canny_edge(self) -> None:
        """Canny 边缘检测：输出图像中的边缘（白线）与非边缘区域（黑色）。

        采用简化版 Canny 流程（经典 Canny 的三大核心步骤）：
        1. 高斯模糊降噪：抑制噪声，避免把噪点误判为边缘
           （滤波前先按边缘像素复制扩展边界，避免图像四周产生虚假边缘）；
        2. Sobel 梯度幅值：计算每个像素的边缘强度；
        3. 阈值二值化：强度大于阈值的像素判为边缘（255），否则为背景（0）。
        阈值由用户输入（0-255），越大检测到的边缘越少。
        （简化说明：未实现非极大值抑制与双阈值滞后连接，可作为后续扩展点。）
        """
        image = self._require_image()
        if image is None:
            return

        # 1. 灰度化
        gray = image.convert("L")
        # 2. 高斯模糊降噪（先复制扩展 2 像素边界，避免模糊在图像四周产生虚假边缘）
        padded = self._replicate_pad(gray, 2)
        blurred = padded.filter(ImageFilter.GaussianBlur(CANNY_GAUSSIAN_RADIUS))
        # 3. Sobel 梯度幅值（尺寸与 blurred 一致）
        magnitude = self._sobel_magnitude(blurred)
        # 4. 裁剪掉模糊阶段的扩展边界，恢复原图尺寸
        magnitude = magnitude.crop(
            (2, 2, magnitude.width - 2, magnitude.height - 2)
        )

        # 5. 弹出输入框获取边缘强度阈值（0-255，默认 DEFAULT_CANNY_THRESHOLD）
        threshold = simpledialog.askinteger(
            "Canny 边缘检测",
            "请输入边缘强度阈值（0-255）：越大检测到的边缘越少。",
            initialvalue=DEFAULT_CANNY_THRESHOLD,
            minvalue=0,
            maxvalue=255,
            parent=self.root,
        )
        if threshold is None:  # 用户点击“取消”，不执行处理
            return

        # 查找表二值化：边缘强度大于阈值 -> 255（白），否则 -> 0（黑）
        lookup_table = [255 if value > threshold else 0 for value in range(256)]
        self._original_image = magnitude.point(lookup_table)
        self._refresh_display()

    def _not_implemented(self, feature: str) -> None:
        """弹出“功能未实现”提示对话框。

        参数:
            feature: 功能名称，用于在提示信息中展示。
        """
        messagebox.showinfo(
            "提示",
            f"「{feature}」功能暂未实现，将在后续版本中提供，敬请期待！",
            parent=self.root,
        )


def main() -> None:
    """程序入口：创建主窗口并启动 Tk 事件循环。"""
    root = tk.Tk()
    app = ImageApp(root)  # noqa: F841 - app 持有界面状态，随窗口生命周期存活
    root.mainloop()


if __name__ == "__main__":
    main()
