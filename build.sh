#!/bin/bash
# QQ Monitor 打包脚本

echo "=== QQ Monitor 打包脚本 ==="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 打包
echo "开始打包..."
pyinstaller --onefile --windowed \
    --name "QQMonitor" \
    --add-data "README.md:." \
    --hidden-import=PyQt5 \
    --hidden-import=requests \
    --hidden-import=yaml \
    qq_monitor.py

# 检查结果
if [ -f "dist/QQMonitor" ] || [ -f "dist/QQMonitor.exe" ]; then
    echo "打包成功！"
    echo "可执行文件位置: dist/"
    ls -la dist/
else
    echo "打包失败，请检查错误信息"
fi