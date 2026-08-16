@echo off
chcp 65001 >nul
rem ============================================================
rem  AI 图像处理系统 —— 一键打包脚本（Windows）
rem  功能：自动检测 Python 与 PyInstaller，并打包 image_app.py
rem  产物：dist\AI-Image-Processing-System\ 文件夹
rem ============================================================

rem 切换到脚本所在目录，保证相对路径正确
cd /d "%~dp0"

rem 自动选择 Python 解释器：优先 python，找不到则尝试 py -3
where python >nul 2>nul
if errorlevel 1 (
    set "PY_CMD=py -3"
) else (
    set "PY_CMD=python"
)

echo [信息] 使用解释器：%PY_CMD%
echo [信息] 开始打包，请耐心等待...
echo.

%PY_CMD% build_exe.py %*

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方日志后重试。
) else (
    echo.
    echo [完成] 打包成功！可执行文件位于 dist\AI-Image-Processing-System\
    echo        双击其中 AI-Image-Processing-System.exe 即可运行。
)
echo.
pause
