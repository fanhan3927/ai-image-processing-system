# AI 图像处理系统 —— 发布使用说明（Release Notes）

> 适用程序：`image_app.py`（Tkinter + Pillow 桌面应用）
> 打包工具：PyInstaller（单目录模式 `--onedir`）
> 打包产物：`AI-Image-Processing-System.exe`

---

## 一、目录结构

```
image-processing-app/
├── image_app.py          # 主程序（打包入口）
├── build_exe.py          # 打包脚本（可自定义参数）
├── build_exe.bat         # 一键打包批处理（双击即可）
├── app.ico               # 应用图标（缺失时脚本自动生成占位图标）
├── resources/            # 本地资源文件夹（通过 --add-data 一并打包）
├── RELEASE_NOTES.md      # 本文档
├── build/                # 打包中间文件（PyInstaller 工作目录，可随时删除）
└── dist/                 # 打包产物输出目录
    └── AI-Image-Processing-System/   # 单目录模式的完整程序文件夹
        ├── AI-Image-Processing-System.exe   # 主程序（双击运行）
        ├── _internal/                        # 依赖库与资源（勿删除！）
        └── ...（运行所需的所有 DLL / 依赖）
```

---

## 二、如何打包

### 方式一：双击批处理（推荐给非技术用户）

1. 进入 `image-processing-app` 文件夹；
2. 双击 `build_exe.bat`；
3. 等待终端显示 **“打包成功”** 即可；
4. 脚本会自动完成：检查 Python → 安装 PyInstaller（如缺）→ 生成图标（如缺）→ 打包。

### 方式二：命令行手动执行

```bat
:: 进入项目目录
cd image-processing-app

:: 首次使用需安装 PyInstaller（脚本会自动安装，也可手动执行）
python -m pip install --upgrade pyinstaller

:: 执行打包（默认单目录模式）
python build_exe.py

:: 常用可选参数
python build_exe.py --clean             :: 打包前清理缓存（默认已开启）
python build_exe.py --onefile           :: 改为单文件模式（不推荐，启动慢、易被误报）
python build_exe.py --no-auto-install   :: 不自动安装 PyInstaller
python build_exe.py --gen-icon          :: 仅生成占位图标 app.ico
```

### 打包命令详解（核心参数说明）

`build_exe.py` 实际执行的等价命令如下（以默认参数为例）：

```
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --windowed ^
  --name "AI-Image-Processing-System" ^
  --icon app.ico ^
  --add-data "resources;resources" ^
  --add-data "app.ico;." ^
  --hidden-import PIL._tkinter_finder ^
  --distpath dist ^
  --workpath build ^
  --specpath build ^
  image_app.py
```

| 参数 | 作用 |
| --- | --- |
| `--name "AI-Image-Processing-System"` | 指定 EXE 名称 |
| `--onedir` | 单目录模式：生成一个文件夹，内含 EXE 与全部依赖（启动快） |
| `--windowed` | GUI 程序模式：运行时不弹出黑色控制台窗口 |
| `--icon app.ico` | 设置 EXE 图标（Windows 要求 .ico 格式） |
| `--add-data "源路径;目标路径"` | 将本地资源一并打包；**Windows 用分号 `;` 分隔**（Linux/macOS 用冒号 `:`） |
| `--hidden-import PIL._tkinter_finder` | 防止打包后出现 `No module named 'PIL._tkinter_finder'` 错误 |
| `--noconfirm` / `--clean` | 覆盖旧产物 / 清理缓存，避免残留导致异常 |
| `--distpath` / `--workpath` / `--specpath` | 输出目录 / 工作目录 / spec 文件目录，保持项目整洁 |

> **关于“自动包含依赖库”**：PyInstaller 会自动分析 `image_app.py` 的全部
> `import` 语句，将用到的 Tkinter（标准库）、Pillow、numpy、OpenCV 等一并打包，
> **无需手动罗列**。注意：只有代码里真正 `import cv2` 时，OpenCV 才会被打包
> （本程序当前未使用 cv2，故产物中不会包含它，属正常现象）。
> 若以后新增了大型依赖且自动收集不完整，可在 `build_exe.py` 中追加
> `--collect-all cv2`、`--collect-all numpy` 等参数（脚本内有注释示例）。

---

## 三、如何运行 EXE

1. 打包成功后，进入 `dist\AI-Image-Processing-System\` 文件夹；
2. **双击 `AI-Image-Processing-System.exe`** 即可启动程序；
3. 程序界面：点击「打开图像」选择图片，即可使用灰度、阈值化、
   Sobel 锐化、Canny 边缘检测等功能。

> ⚠️ **重要**：单目录模式（`--onedir`）下，EXE 依赖同文件夹内的
> `_internal/` 目录及所有文件。**分发时请打包整个文件夹**（如压缩成 ZIP），
> 不要把 exe 单独拷走，否则程序无法启动。

---

## 四、如何分发

1. 将 `dist\AI-Image-Processing-System\` 整个文件夹压缩为 ZIP；
2. 发给用户后，对方解压即可运行，**无需安装 Python 环境**；
3. 若需要安装包形式（带开始菜单快捷方式、卸载入口），可使用：
   - [Inno Setup](https://jrsoftware.org/isinfo.php)（免费，推荐）
   - [NSIS](https://nsis.sourceforge.io/)（免费）
   - 或 WinRAR / 7-Zip 自解压包（最简单）

---

## 五、程序内读取打包资源的方法

`--add-data` 打包的资源在运行时位于 `sys._MEIPASS` 指向的目录。
在 `image_app.py` 中添加以下工具函数即可统一访问（开发环境与打包后均适用）：

```python
import os
import sys

def resource_path(relative: str) -> str:
    """返回资源文件绝对路径：兼容开发环境与 PyInstaller 打包环境。"""
    # 打包后 sys._MEIPASS 指向程序内部目录（_internal）；开发时用脚本所在目录
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

# 示例：读取 resources/ 中的图片，或为窗口设置 app.ico 图标
# img_path = resource_path(os.path.join("resources", "logo.png"))
# root.iconbitmap(resource_path("app.ico"))
```

---

## 六、常见问题（FAQ）

| 问题 | 解决方法 |
| --- | --- |
| 双击 EXE 无反应 / 一闪而过 | 在 `dist\AI-Image-Processing-System\` 文件夹中按住 Shift 右键 → “在此处打开 PowerShell 窗口”，输入 `.\AI-Image-Processing-System.exe` 查看报错信息；也可用 `--windowed` 改为临时去掉后重打包看控制台输出 |
| 杀毒软件（如 Windows Defender）报毒/误报 | PyInstaller 打包的程序常被启发式误报。可：① 在杀软中加白名单；② 用 **UPX 以外的方案**重新打包（脚本未用 UPX）；③ 代码签名（购买/申请证书，最彻底） |
| 提示缺少 `VCRUNTIME140.dll` / `MSVCP140.dll` | 目标电脑缺少 VC++ 运行库，安装 [微软 VC++ 2015-2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) 即可 |
| 提示 `No module named 'PIL._tkinter_finder'` | 已在打包命令中加入 `--hidden-import PIL._tkinter_finder`，若仍出现请升级 PyInstaller：`python -m pip install -U pyinstaller` |
| 打包体积过大 | 在 `build_exe.py` 中追加 `--exclude-module` 排除未使用的模块（如 `matplotlib`、`scipy` 等） |
| 想把 `resources` 之外的文件也打包 | 在 `build_exe.py` 的 `RESOURCE_DIRS` 元组中追加文件夹名，或直接在命令行加 `--add-data "源;目标"` |
| 想换正式图标 | 用任意图片制作工具导出 `app.ico`（含 256x256 尺寸），替换项目根目录的 `app.ico` 后重新打包 |

---

## 七、版本记录

| 版本 | 说明 |
| --- | --- |
| v1.0 | 首次发布：单目录模式打包，含资源目录与图标支持 |
