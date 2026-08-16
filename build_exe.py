# -*- coding: utf-8 -*-
"""
=====================================================================
 build_exe.py —— AI 图像处理系统 打包脚本（Windows / PyInstaller）
=====================================================================

【脚本功能】
    将主程序 image_app.py 打包为 Windows 可执行程序（EXE）：
        - 输出名称：AI-Image-Processing-System.exe
        - 打包模式：单目录模式（--onedir），产物位于 dist/AI-Image-Processing-System/
        - 自动收集依赖：Tkinter（Python 标准库）、Pillow、OpenCV(cv2) 等
          （PyInstaller 会自动分析主程序 import 的所有模块并一并打包，
            不需要在命令行里手动罗列依赖，详见下方“依赖收集说明”）
        - 本地资源文件：resources/ 目录（通过 --add-data 打包进程序目录）
        - 应用图标：app.ico（缺失时自动生成一个占位图标，保证打包不中断）

【使用方法】
    方式一（推荐）：在 image-processing-app 文件夹中直接双击 build_exe.bat
    方式二（命令行）：
        python build_exe.py                    # 全部使用默认参数打包
        python build_exe.py --clean            # 打包前强制清理缓存（默认开启）
        python build_exe.py --no-auto-install  # 不自动安装 PyInstaller（需已安装）
        python build_exe.py --gen-icon         # 仅生成占位图标 app.ico，不打包

【目录结构约定】
    image-processing-app/
    ├── image_app.py      # 主程序（打包入口脚本）
    ├── build_exe.py      # 本打包脚本
    ├── build_exe.bat     # 一键打包批处理（双击即可）
    ├── app.ico           # 应用图标（缺失时脚本会自动生成）
    ├── resources/        # 本地资源文件夹（会被 --add-data 整体打包）
    └── dist/             # 打包产物输出目录（脚本自动创建）

【依赖收集说明】
    PyInstaller 会静态分析 image_app.py 及其所有 import 语句，把用到的
    第三方库（Pillow、numpy、cv2 等）连同解释器动态库一起打包，因此：
        - Tkinter：Python 标准库，自动包含；
        - Pillow：只要代码里 import 了 PIL，就会自动打包；
        - OpenCV：只有代码里真正 `import cv2` 才会被打包；
          （本程序当前未使用 cv2，故产物中不会包含它，属正常现象）
        - 若未来新增依赖且打包后运行报缺模块，可在下方 build_args
          中添加 --hidden-import 或 --collect-all 参数（见代码注释）。

【打包后运行】
    双击 dist/AI-Image-Processing-System/AI-Image-Processing-System.exe 即可。
    注意：单目录模式（--onedir）下必须连同整个文件夹一起分发，
          不能只拷贝其中的 exe 文件（详细说明见 RELEASE_NOTES.md）。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# ================================================================
# 常量配置（可根据项目实际情况修改）
# ================================================================
PROJECT_DIR = Path(__file__).resolve().parent   # 项目根目录 = 脚本所在目录
ENTRY_SCRIPT = PROJECT_DIR / "image_app.py"     # 主程序入口脚本
APP_NAME = "AI-Image-Processing-System"         # 生成的 EXE 名称
ICON_FILE = PROJECT_DIR / "app.ico"             # 应用图标文件
RESOURCE_DIRS = ("resources", "assets")         # 需要随程序打包的本地资源文件夹
MIN_PYTHON = (3, 8)                             # 要求的最低 Python 版本


def check_environment() -> None:
    """检查运行环境：Python 版本与主程序文件是否存在。"""
    if sys.version_info < MIN_PYTHON:
        sys.exit(
            f"[错误] 当前 Python 版本过低（{sys.platform}），"
            f"至少需要 Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}。"
        )
    if not ENTRY_SCRIPT.is_file():
        sys.exit(f"[错误] 未找到主程序文件：{ENTRY_SCRIPT}")


def ensure_pyinstaller(auto_install: bool) -> bool:
    """确保 PyInstaller 可用。

    返回:
        True 表示 PyInstaller 可正常调用；False 表示不可用。
    """
    try:
        # 尝试直接导入，验证 PyInstaller 是否已安装
        import PyInstaller  # noqa: F401 - 仅用于探测安装状态
        print("[信息] 已检测到 PyInstaller。")
        return True
    except ImportError:
        pass

    if not auto_install:
        print(
            "[错误] 未检测到 PyInstaller，请先手动安装：\n"
            "       pip install pyinstaller\n"
            "       或重新运行本脚本（默认会自动安装）。"
        )
        return False

    print("[信息] 未检测到 PyInstaller，正在自动安装（pip install -U pyinstaller）...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]
    )
    if result.returncode != 0:
        print("[错误] PyInstaller 安装失败，请检查网络或手动执行上述命令。")
        return False
    print("[信息] PyInstaller 安装完成。")
    return True


def generate_placeholder_icon() -> bool:
    """生成占位图标 app.ico（使用 Pillow 绘制）。

    当项目中没有 app.ico 时调用，保证打包命令中的 --icon 参数有文件可用；
    用户后期可自行用任意 .ico 文件替换。
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[警告] 未安装 Pillow，无法自动生成图标；请手动提供 app.ico 后重试。")
        return False

    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 绘制圆角蓝色底 + 白色“AI”文字（简洁占位样式）
    draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=48, fill=(37, 99, 235, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 110)  # Windows 自带字体
    except OSError:
        font = ImageFont.load_default()               # 找不到字体时退回默认字体
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
        text, font=font, fill=(255, 255, 255, 255),
    )

    # 保存为多尺寸 ICO，Windows 会根据显示场景自动选用合适尺寸
    image.save(ICON_FILE, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                 (64, 64), (128, 128), (256, 256)])
    print(f"[信息] 已自动生成占位图标：{ICON_FILE.name}（可自行替换为正式图标）")
    return True


def collect_add_data() -> list[str]:
    """收集需要随程序打包的本地资源文件，生成 --add-data 参数列表。

    --add-data 语法（Windows 使用分号分隔）：
        "源路径;目标路径"
    其中目标路径是相对打包后程序内部目录（_internal）的路径，
    运行时可用 sys._MEIPASS 拼接得到绝对路径（见 RELEASE_NOTES.md 示例）。

    返回:
        形如 ["resources;resources", "app.ico;.", ...] 的参数列表。
    """
    items: list[str] = []

    # 1) 打包 resources/、assets/ 等本地资源文件夹（存在才打包）
    for folder_name in RESOURCE_DIRS:
        folder = PROJECT_DIR / folder_name
        if folder.is_dir():
            # 源路径;目标路径 —— 目标路径与文件夹同名，便于运行时定位
            items.append(f"{folder};{folder_name}")
            print(f"[信息] 已加入资源文件夹：{folder_name}/")
        else:
            print(f"[信息] 未发现 {folder_name}/ 文件夹，跳过（可选资源）。")

    # 2) 将 app.ico 也打包进程序内部，供程序运行时设置窗口图标
    if ICON_FILE.is_file():
        items.append(f"{ICON_FILE};.")
        print("[信息] 已加入运行时图标：app.ico")

    return items


def run_pyinstaller(args: argparse.Namespace, add_data: list[str]) -> int:
    """组装并执行 PyInstaller 打包命令。

    参数:
        args: 命令行解析出的参数（--clean / --onefile 等）。
        add_data: 收集好的 --add-data 参数列表。
    返回:
        PyInstaller 子进程的退出码（0 表示成功）。
    """
    dist_dir = PROJECT_DIR / "dist"   # 打包产物输出目录
    build_dir = PROJECT_DIR / "build" # PyInstaller 工作目录（存放临时文件与 .spec）

    # ---------------- 组装 PyInstaller 参数 ----------------
    build_args: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",                 # 覆盖已存在的输出目录，无需二次确认
        "--clean",                     # 每次打包前清理缓存，避免旧文件残留
        "--onedir" if not args.onefile else "--onefile",  # 单目录模式（默认）
        "--windowed",                  # GUI 程序：不弹出黑色控制台窗口
        "--name", APP_NAME,            # 可执行文件名称
        "--icon", str(ICON_FILE),      # 应用图标（要求 .ico 格式）
        "--distpath", str(dist_dir),   # 指定输出目录
        "--workpath", str(build_dir),  # 指定工作目录
        "--specpath", str(build_dir),  # 指定 .spec 文件存放目录（保持项目整洁）
        # 防御性隐藏导入：PIL.ImageTk 在打包后可能找不到 _tkinter_finder，
        # 提前显式声明可避免经典的“No module named 'PIL._tkinter_finder'”错误
        "--hidden-import", "PIL._tkinter_finder",
        # 若程序以后新增了重型依赖且自动收集不完整，可在此追加，例如：
        # "--collect-all", "cv2",      # 强制收集 OpenCV 的全部子模块与数据
        # "--collect-all", "numpy",    # 强制收集 numpy 的全部子模块
        # "--exclude-module", "matplotlib",  # 排除用不到的模块以缩小体积
    ]

    # 追加 --add-data 资源参数（核心需求：将本地资源一并打包）
    for item in add_data:
        build_args += ["--add-data", item]

    # 最后一个参数是打包入口脚本
    build_args.append(str(ENTRY_SCRIPT))

    # ---------------- 打印将要执行的完整命令（便于核对/复制） ----------------
    print("\n[信息] 即将执行打包命令：")
    print("    " + " ".join(build_args))
    print(f"[信息] 开始打包，请耐心等待（首次打包需 1-5 分钟）...\n")

    # ---------------- 执行打包 ----------------
    # stdout/stderr 不重定向，让 PyInstaller 的进度信息实时显示在终端。
    # 注意：Windows 上 --clean 清理旧 build 目录时，若某文件正被占用
    # （例如杀毒软件扫描、资源管理器预览、上一条命令刚释放句柄等），
    # 会抛出 WinError 32 “文件正由另一进程使用”导致打包失败；
    # 这类锁通常是瞬时的，因此失败后自动重试数次。
    MAX_ATTEMPTS = 3          # 最多尝试次数
    RETRY_DELAY_SECONDS = 3   # 每次失败后的等待秒数
    last_code = -1
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = subprocess.run(build_args, cwd=PROJECT_DIR)
        last_code = result.returncode
        if last_code == 0:
            break
        if attempt < MAX_ATTEMPTS:
            print(f"\n[信息] 打包失败（退出码 {last_code}），"
                  f"等待 {RETRY_DELAY_SECONDS} 秒后自动重试（第 {attempt + 1}/{MAX_ATTEMPTS} 次）...")
            time.sleep(RETRY_DELAY_SECONDS)
    return last_code


def verify_output(onefile: bool) -> Path | None:
    """校验打包产物是否生成成功。

    返回:
        生成的 EXE 文件路径；未找到时返回 None。
    """
    if onefile:
        exe_path = PROJECT_DIR / "dist" / f"{APP_NAME}.exe"
    else:
        exe_path = PROJECT_DIR / "dist" / APP_NAME / f"{APP_NAME}.exe"
    return exe_path if exe_path.is_file() else None


def print_release_guide(onefile: bool) -> None:
    """打包成功后输出简要发布说明（详细说明见 RELEASE_NOTES.md）。"""
    exe = verify_output(onefile)
    print("\n" + "=" * 60)
    print("  打包成功！")
    print("=" * 60)
    print(f"  可执行文件位置：{exe}")
    if not onefile:
        print("  （单目录模式）运行/分发时请保留 exe 所在的整个文件夹：")
        print(f"  {exe.parent}")
    print()
    print("  运行方式：双击上面的 exe 文件即可启动程序。")
    print("  发布说明：详见 RELEASE_NOTES.md（运行、分发、常见问题）。")
    print("=" * 60 + "\n")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AI 图像处理系统打包脚本（PyInstaller，Windows EXE）"
    )
    parser.add_argument(
        "--onefile", action="store_true",
        help="使用单文件模式（默认单目录模式 --onedir）",
    )
    parser.add_argument(
        "--clean", action="store_true", default=True,
        help="打包前清理缓存（默认开启）",
    )
    parser.add_argument(
        "--no-auto-install", action="store_true",
        help="不自动安装 PyInstaller（未安装时直接报错退出）",
    )
    parser.add_argument(
        "--gen-icon", action="store_true",
        help="仅生成占位图标 app.ico，不执行打包",
    )
    return parser.parse_args()


def configure_console_encoding() -> None:
    """统一控制台输出编码，避免在 GBK 等旧代码页下打印特殊字符时崩溃。

    例如在中文 Windows 的 cmd 中默认代码页为 cp936（GBK），
    直接 print 某些符号（如 🎉）会抛出 UnicodeEncodeError；
    这里将 stdout/stderr 重配置为 UTF-8 并开启 errors="replace"
    （无法显示的字符以 ? 替代而不是抛异常），保证脚本任何环境下都不崩溃。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            # 极老版本 Python 没有 reconfigure，忽略即可（不影响主流程）
            pass


def main() -> int:
    """打包流程主入口。"""
    configure_console_encoding()
    args = parse_args()

    # 特殊模式：仅生成图标
    if args.gen_icon:
        return 0 if generate_placeholder_icon() else 1

    # 1. 环境检查
    check_environment()

    # 2. 确保 PyInstaller 可用
    if not ensure_pyinstaller(auto_install=not args.no_auto_install):
        return 1

    # 3. 确保图标存在（--icon 参数要求文件必须存在）
    if not ICON_FILE.is_file() and not generate_placeholder_icon():
        print("[错误] 缺少 app.ico 且无法自动生成，打包终止。")
        return 1

    # 4. 收集本地资源（--add-data）
    add_data = collect_add_data()

    # 5. 执行打包
    returncode = run_pyinstaller(args, add_data)
    if returncode != 0:
        print(f"\n[错误] 打包失败（PyInstaller 退出码 {returncode}），"
              f"请查看上方日志。")
        return returncode

    # 6. 校验产物并输出发布说明
    if verify_output(args.onefile) is None:
        print("[错误] 未找到打包产物，请检查上方日志。")
        return 1
    print_release_guide(args.onefile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
