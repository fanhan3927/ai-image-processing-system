本文件夹（resources/）用于存放需要随 EXE 一起打包的本地资源文件，
例如：示例图片、程序 Logo、配置文件、字体文件等。

打包时 build_exe.py 会通过 --add-data 参数将本文件夹整体复制进
程序内部目录（_internal/resources/），运行时可用以下代码访问：

    import os, sys
    def resource_path(relative):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, relative)

    # 示例：读取本文件夹中的 logo.png
    # path = resource_path(os.path.join("resources", "logo.png"))

注意：
1. 本说明文件（README.txt）会随文件夹一并打包，正式发布前可删除。
2. 若项目中没有本文件夹，build_exe.py 会自动跳过 --add-data，
   不影响打包。
