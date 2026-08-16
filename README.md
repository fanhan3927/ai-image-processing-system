# AI Image Processing System（AI 图像处理系统）

基于 **Python + Tkinter + Pillow** 构建的桌面图像处理应用。界面采用 Frame + Grid
简洁布局：上部为功能按钮区，下部为图像显示区（Pillow 等比缩放适配窗口，
拖拽窗口自动重适配）。支持一键打包为 Windows EXE 分发，目标机器无需安装 Python。

## ✨ 功能特性

| 按钮 | 功能 | 实现说明 |
|---|---|---|
| 📂 打开图像 | 文件对话框选择本地图像 | 支持 png/jpg/jpeg/bmp/gif/tiff/webp，异常文件有错误提示 |
| ⚫ 图像灰度处理 | 转换为 8 位灰度图 | `convert("L")`，模式转换 |
| ⚪ 图像阈值化 | 二值化（黑白） | 输入阈值（默认 128），查找表逐像素映射 |
| ✨ Sobel 锐化 | 突出图像边缘 | Sobel 梯度幅值叠加到原灰度图 |
| 🔍 Canny 边缘 | 边缘检测 | 高斯降噪 + Sobel 梯度 + 阈值二值化（简化版 Canny） |
| 🖥 界面自适应 | 窗口缩放图像自动重排 | 监听 `<Configure>` 事件 |

> 「图像平移」「直方图均衡化」「均值滤波」为预留入口，当前点击会提示
> “功能暂未实现”，后续版本实现（在 `_build_button_area` 中注册回调即可扩展）。

## 📥 下载与运行（无需安装 Python）

从 **[GitHub Releases](https://github.com/fanhan3927/AI-Image-Processing-System/releases)**
下载最新的 `AI-Image-Processing-System-vX.Y.Z-win64.zip`：

1. 解压 ZIP；
2. 双击 `AI-Image-Processing-System\AI-Image-Processing-System.exe`；
3. 点击「打开图像」选择图片即可使用各项功能。

> ⚠️ 单目录模式下，`AI-Image-Processing-System.exe` 依赖同文件夹内的
> `_internal\` 目录，请保留整个文件夹，不要单独拷贝 exe。
> 若被杀毒软件误报，请在杀软中添加信任（PyInstaller 打包程序常见误报）。

## 🛠 本地开发运行

```bash
:: 1. 安装依赖（Python 3.8+）
pip install -r requirements.txt

:: 2. 运行程序
python image_app.py
```

## 📦 打包为 Windows EXE

```bat
:: 方式一：直接双击 build_exe.bat（自动安装 PyInstaller 并打包）

:: 方式二：命令行
python build_exe.py                 :: 默认单目录模式（--onedir）
python build_exe.py --onefile       :: 可选：单文件模式
python build_exe.py --gen-icon      :: 仅生成占位图标 app.ico
```

打包产物位于 `dist\AI-Image-Processing-System\`，包含：

- `AI-Image-Processing-System.exe` —— 主程序（含 `app.ico` 图标）
- `_internal\` —— 全部依赖库与本地资源（`resources\`、图标等）

`build_exe.py` 自动完成：检查/安装 PyInstaller → 缺失时生成占位图标 →
自动收集依赖（Tkinter、Pillow 等）→ 通过 `--add-data` 打包本地资源 →
输出 EXE（失败自动重试）。详细参数说明与常见问题见 [RELEASE_NOTES.md](RELEASE_NOTES.md)。

## 📁 目录结构

```
image-processing-app/
├── image_app.py      # 主程序（打包入口）
├── build_exe.py      # PyInstaller 打包脚本
├── build_exe.bat     # 一键打包批处理
├── app.ico           # 应用图标
├── resources/        # 本地资源文件夹（随 EXE 一并打包）
├── requirements.txt  # 运行依赖
├── RELEASE_NOTES.md  # 发布使用说明
└── dist/             # 打包产物（本地生成，不入库）
```

## 🧰 技术栈

- **Python 3.8+** / Tkinter（GUI）/ Pillow（图像处理）
- **PyInstaller 6.x**（打包，`--onedir` 单目录模式）

## 📄 许可证

本项目仅供学习交流使用，暂未指定开源许可证。
