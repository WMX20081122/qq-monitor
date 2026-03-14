#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台打包脚本
注意：PyInstaller 只能打包当前系统的可执行文件
如需跨平台打包，请在对应系统上运行此脚本
"""

import os
import sys
import platform
import subprocess

def build():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    print(f"当前系统: {system} {machine}")
    print("开始打包...")
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "QQMonitor",
        "--hidden-import=PyQt5",
        "--hidden-import=requests", 
        "--hidden-import=yaml",
        "qq_monitor.py"
    ]
    
    # Linux/Mac 不需要 --windowed (会报错)
    if system != "windows":
        cmd.remove("--windowed")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("打包成功！")
        output_dir = "dist"
        if os.path.exists(output_dir):
            print(f"输出文件: {os.listdir(output_dir)}")
    else:
        print(f"打包失败: {result.stderr}")

if __name__ == "__main__":
    build()
